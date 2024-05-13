import json
import os
import re

import requests


class LLM_Evaluator:
    def __init__(
        self,
        model_to_eval: str = "llama2",
        evaluator_model: str = "llama3",
        dataset_path: str = "data/zero_shot/dataset.jsonl",
    ):
        self.__model_to_eval = model_to_eval
        self.__evaluator_model = evaluator_model
        self.__dataset = self.__load_dataset(dataset_path)

    def answer_questions(
        self, output_path: str = "data/evaluation/generated_output.jsonl"
    ):
        # Check if the directory exists
        os.makedirs("data/evaluation", exist_ok=True)

        # Generate the output of the model to evaluate
        with open(output_path, "a") as f:
            for data in self.__dataset:
                try:
                    output_text = ""

                    # Generate the output using the model to evaluate
                    while not output_text:
                        output_text = self.__generate_response(
                            context=data["context"],
                            question=data["prompt"],
                            model=self.__model_to_eval,
                        )

                    # Dump the generated output to a file
                    f.write(
                        json.dumps(
                            {"prompt": data["prompt"], "generated_output": output_text}
                        )
                        + "\n"
                    )
                except Exception as error:
                    print(
                        f"{error.__class__.__name__}[{error.__traceback__.tb_lineno}]: {error}"
                    )
            f.close()

    def evaluate_model(
        self, generated_output_path: str = "data/evaluation/generated_output.jsonl"
    ):
        # Load the generated output
        generated_output = self.__load_dataset(generated_output_path)

        # Delete the extension of the generated output path
        generated_output_path = generated_output_path.split("/")[-1].split(".")[0]

        with open(
            f"data/evaluation/evaluation_{generated_output_path}.jsonl", "a"
        ) as f:
            for i, generated_answer in enumerate(generated_output):
                try:
                    # Get the prompt and the generated answer
                    generated_answer = generated_answer["generated_output"]

                    # Get the real answer
                    real_answer = self.__dataset[i]["answer"]

                    # Evaluate the generated answer with the evaluator model

                    context = r'You are a model used to evaluate if this answer of other model is well answered, you ONLY can answer with this json format: {"is_correct": "Yes" or "No", "punctuation": <Number from 0 to 100 with how good is the question answered>}. Every other format answer will be considered as wrong.'

                    input_text = f"Model to evaluate answer: {generated_answer}\nReal answer:\n{real_answer}"

                    output_text = ""
                    number_of_tries = 0

                    while not output_text:
                        output_text = self.__generate_response(
                            context=context,
                            question=input_text,
                            model=self.__evaluator_model,
                        )

                        # If output text is not like the expected, try again
                        if not re.match(
                            r'{"is_correct": "(Yes|No)", "punctuation": \d{1,3}}',
                            output_text,
                        ):
                            output_text = ""
                            print(
                                "Output text format is not like the expected, trying again."
                            )
                            number_of_tries += 1
                            if number_of_tries > 10:
                                print(
                                    "The model to evaluate the answer is not working properly, writing default answer and note and going to next question."
                                )
                                output_text = '{"is_correct": "No", "punctuation": 0, "note": "Model to evaluate the answer is not working properly"}'

                    # Convert the output text to a dictionary
                    final_output = json.loads(output_text)

                    # Dump the evaluation to a file
                    f.write(
                        json.dumps(
                            {
                                "prompt": input_text,
                                "evaluation": final_output,
                            }
                        )
                        + "\n"
                    )
                except Exception as error:
                    print(
                        f"{error.__class__.__name__}[{error.__traceback__.tb_lineno}]: {error}"
                    )
            f.close()

    def generate_report(self, evaluation_input: str):
        # Load the generated output
        generated_output = self.__load_dataset(evaluation_input)

        data_per_question = {}

        for i in range(9):
            data_per_question[f"question{i}"] = {
                "correct": 0,
                "problematic_eval": 0,
                "total": 0,
                "total_punct": 0,
            }

        for i, generated_answer in enumerate(generated_output):
            try:
                # Get the evaluation
                evaluation = generated_answer["evaluation"]

                # Get the punctuation
                punctuation = evaluation["punctuation"]

                # Update the data_per_question dictionary
                data_per_question[f"question{i % 9}"]["total"] += 1

                if evaluation["is_correct"] == "Yes":
                    data_per_question[f"question{i % 9}"]["correct"] += 1

                data_per_question[f"question{i % 9}"]["total_punct"] += punctuation

                # If evaluation has a note, increment the problematic_eval counter
                if "note" in evaluation:
                    data_per_question[f"question{i % 9}"]["problematic_eval"] += 1

            except Exception as error:
                print(
                    f"{error.__class__.__name__}[{error.__traceback__.tb_lineno}]: {error}"
                )

        # Print general report and report separated by question
        print("----------------")
        print("General report")
        print("----------------")

        total_correct = 0
        total_problematic_eval = 0
        total_total = 0
        total_total_punct = 0

        for data in data_per_question.values():
            total_correct += data["correct"]
            total_problematic_eval += data["problematic_eval"]
            total_total += data["total"]
            total_total_punct += data["total_punct"]

        print(f"Total correct answers: {total_correct}")
        print(f"Total problematic evaluations: {total_problematic_eval}")
        print(f"Total questions: {total_total}")
        print(
            f"Average punctuation: {total_total_punct / total_total if total_total != 0 else 0}"
        )

        print("----------------")
        print("Report by question")
        print("----------------")

        # Print the report
        for i in range(9):
            try:
                correct = data_per_question[f"question{i}"]["correct"]
                total = data_per_question[f"question{i}"]["total"]
                total_punct = data_per_question[f"question{i}"]["total_punct"]
                problematic_eval = data_per_question[f"question{i}"]["problematic_eval"]

                print(
                    f"Question {i}: Correct: {correct}/{total} ({round(correct / total * 100, 2) if total != 0 else 0}%), Average punctuation: {round(total_punct / total, 2) if total != 0 else 0}, Problematic evaluations: {problematic_eval}"
                )
            except Exception as error:
                print(
                    f"{error.__class__.__name__}[{error.__traceback__.tb_lineno}]: {error}"
                )

    def __load_dataset(self, dataset_path: str):
        dataset = []
        try:
            with open(os.path.join(os.getcwd(), dataset_path), "r") as f:
                for line in f:
                    dataset.append(json.loads(line))
        except Exception as error:
            print(
                f"{error.__class__.__name__}[{error.__traceback__.tb_lineno}]: {error}"
            )
        return dataset

    def __generate_response(
        self,
        context: str,
        question: str,
        model: str,
        url: str = "http://localhost:11434/api/generate",
    ) -> str:
        response_text = ""
        # Check if the Ollama API is running
        if requests.get("http://localhost:11434").text != "Ollama is running":
            print("Ollama is not running, please start the Ollama API to continue.")
            # Block the execution of the program until user press a key
            input("Press any key to continue...")
        try:
            # Generate the output using HTTP Ollama API
            data = {
                "model": model,
                "system": context,
                "prompt": question,
                "stream": False,
                "options": {
                    "temperature": 0,
                },
            }

            response = requests.post(url, data=json.dumps(data))

            if response.status_code == 200:
                response_text = json.loads(response.text)["response"]
            else:
                print(f"Error: {response.status_code}")

        except Exception as error:
            print(
                f"{error.__class__.__name__}[{error.__traceback__.tb_lineno}]: {error}"
            )
        return response_text
