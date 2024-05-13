import os

import click

from dataset.dataset import Dataset
from lib.clean_raw_data import clean_raw_data
from llm_eval.llm_eval import LLM_Evaluator
from scraper.scraper import Scraper


@click.group()
def wireshairk():
    click.echo("--------------------")
    click.echo("     Wireshairk")
    click.echo("--------------------")


@wireshairk.command()
def scrape():
    click.echo("Scraping")
    scraper = Scraper()
    scraper.download_captures()


@wireshairk.command()
def clean_raw():
    click.echo("Cleaning raw data")
    clean_raw_data()


@wireshairk.command()
def scrape_and_clean():
    click.echo("Scraping and cleaning raw data")
    scraper = Scraper()
    scraper.download_captures()
    clean_raw_data()


@wireshairk.command()
@click.option("--data_path", default="data/cleaned/", help="Path to the data folder")
@click.option(
    "--zero_shot",
    is_flag=True,
    default=True,
    show_default=True,
    help="Generate zero shot dataset",
)
@click.option(
    "--one_shot", is_flag=True, default=False, help="Generate one shot dataset"
)
@click.option(
    "--chain_of_thought",
    is_flag=True,
    default=False,
    help="Generate chain-of-thought dataset",
)
def generate_dataset(data_path, zero_shot, one_shot, chain_of_thought):
    click.echo("Generating dataset")
    dataset = Dataset(os.path.join(os.getcwd(), data_path))
    capture_example = """
    No.|Time|Source|Destination|Protocol|Length|Port src.|Port dst.|Info
    1 0.000000 145.254.160.237 -> 65.208.228.223 TCP 62 3372 -> 80 [SYN] Seq=0 Win=8760 Len=0 MSS=1460 SACK_PERM
    2 0.911310 65.208.228.223 -> 145.254.160.237 TCP 62 80 -> 3372 [SYN, ACK] Seq=0 Ack=1 Win=5840 Len=0 MSS=1380 SACK_PERM
    3 0.911310 145.254.160.237 -> 65.208.228.223 TCP 54 3372 -> 80 [ACK] Seq=1 Ack=1 Win=9660 Len=0
    4 0.911310 145.254.160.237 -> 65.208.228.223 HTTP 533 GET /download.html HTTP/1.1"""
    questions = dataset.get_questions()

    if one_shot:
        click.echo("##############################")
        click.echo("Generating one shot dataset")
        click.echo("##############################")
        dataset.generate_dataset(
            "one_shot",
            [
                f"{capture_example}\nQ: {questions[0]}\nA: In the capture there are a total of 4 packets",
                f"{capture_example}\nQ: {questions[1]}\nA: There are a total of 2 unique communicators in the trace. These are the IPs: 145.254.160.237, 65.208.228.223",
                f"{capture_example}\nQ: {questions[2]}\nA: The IP that participates the most in the communication is the IP 145.254.160.237",
                f"{capture_example}\nQ: {questions[3]}\nA: The total size of transmitted bytes is 711 bytes",
                f"{capture_example}\nQ: {questions[4]}\nA: The average size of packets in bytes is 177.75 bytes",
                f"{capture_example}\nQ: {questions[5]}\nA: In the capture predominates the use of TCP",
                f"{capture_example}\nQ: {questions[6]}\nA: The communication lasts 0.91131 seconds",
                f"{capture_example}\nQ: {questions[7]}\nA: The average of packets sent per second is 4.39",
                f"{capture_example}\nQ: {questions[8]}\nA: The average bytes/s sent in the communication is 779.03",
            ],
        )
    elif chain_of_thought:
        click.echo("##############################")
        click.echo("Generating Chain-of-Thought dataset")
        click.echo("##############################")
        dataset.generate_dataset(
            "chain_of_thought",
            [
                f"{capture_example}\nQ: {questions[0]}\nA: The last row of the capture No column is 4. So the total number of packets in the trace is 4",
                f"{capture_example}\nQ: {questions[1]}\nA: In the first row, the Source and Destination columns show the IPs 145.254.160.237 and 65.208.228.223, this IPs never appear before so there are 2 unique communicators for now. In the second row, 65.208.228.223 and 145.254.160.237 appear again, so we don't add new communicators. In the row three and four the IPs 65.208.228.223 and 145.254.160.237 repeat again so we can not add new communicators. So there is not more rows, we can conclude that there are a total of 2 unique communicators in the trace. These are the IPs: 145.254.160.237 and 65.208.228.223",
                f"{capture_example}\nQ: {questions[2]}\nA: Aparition IP counter: First row: 145.254.160.237: 1 occurrence, 65.208.228.223: 1 occurrence // Second row: 145.254.160.237: 2 occurrence, 65.208.228.223 2 occurrences // Third row: 145.254.160.237: 3 occurrence, 65.208.228.223 3 occurrences // Fourth row: 145.254.160.237: 4 occurrence, 65.208.228.223 4 occurrences. So the IP that participates the most in the communication is the IP 145.254.160.237",
                f"{capture_example}\nQ: {questions[3]}\nA: The first packet has a length of 62 bytes, the second packet has a length of 62 bytes, the third packet has a length of 54 bytes and the fourth packet has a length of 533 bytes. So the total size of transmitted bytes is 62+62+54+533=711 bytes",
                f"{capture_example}\nQ: {questions[4]}\nA: The first packet has a length of 62 bytes, the second packet has a length of 62 bytes, the third packet has a length of 54 bytes and the fourth packet has a length of 533 bytes. So the average size of packets in bytes is (62+62+54+533)bytes/(4)packets=(177.75)bytes/packet",
                f"{capture_example}\nQ: {questions[5]}\nA: The first packet has a protocol of TCP, the second packet has a protocol of TCP, the third packet has a protocol of TCP and the fourth packet has a protocol of HTTP. So in the capture predominates the use of TCP",
                f"{capture_example}\nQ: {questions[6]}\nA: The last packet has a time of 0.911310 seconds and the first packet has a time of 0.000000 seconds. So the communication lasts 0.91131-0.000000=0.91131 seconds",
                f"{capture_example}\nQ: {questions[7]}\nA: The last packet has a time of 0.911310 seconds and the first packet has a time of 0.000000 seconds. So the communication lasts 0.91131-0.000000=0.91131 seconds. The total number of packets in the trace is 4. So the average of packets sent per second is (4)packets/(0.91131)seconds=(4.39)packets/second",
                f"{capture_example}\nQ: {questions[8]}\nA: The last packet has a time of 0.911310 seconds and the first packet has a time of 0.000000 seconds. So the communication lasts 0.91131-0.000000=0.91131 seconds. The total size of transmitted bytes is 62+62+54+533=711 bytes. So the average bytes/s sent in the communication is (711)bytes/(0.91131)seconds=(779.03)bytes/second",
            ],
        )
    else:
        click.echo("##############################")
        click.echo("Generating zero shot dataset")
        click.echo("##############################")
        dataset.generate_dataset(
            "zero_shot",
            10 * [""],
        )


@wireshairk.command()
@click.option("--model", default="llama2", help="Model to evaluate")
@click.option(
    "--dataset_path", default="data/zero_shot/dataset.jsonl", help="Path to the dataset"
)
@click.option(
    "--output_path",
    default="data/evaluation/generated_output_llama2.jsonl",
    help="Path to the generated output file",
)
def answer_questions(model, dataset_path, output_path):
    click.echo(f"Answering questions for model: {model}")
    evaluator = LLM_Evaluator(model_to_eval=model, dataset_path=dataset_path)
    evaluator.answer_questions(output_path=output_path)


@wireshairk.command()
@click.option(
    "--generated_output",
    default="data/evaluation/generated_output_llama2.jsonl",
    help="Path to the generated output file",
)
def evaluate(generated_output):
    click.echo("Generating report")
    # Extract the name of evaluated model from the generated_output path
    model = generated_output.split("/")[-1].split("_")[-1].split(".")[0]
    evaluator = LLM_Evaluator(model_to_eval=model)
    evaluator.evaluate_model(generated_output_path=generated_output)


@wireshairk.command()
@click.option(
    "--evaluation_input", default="data/evaluation/generated_output_llama2.jsonl"
)
def generate_report(evaluation_input):
    model = evaluation_input.split("/")[-1].split("_")[-1].split(".")[0]
    click.echo(f"Generating report for model: {model}")
    evaluator = LLM_Evaluator(model_to_eval=model)
    evaluator.generate_report(evaluation_input)


if __name__ == "__main__":
    wireshairk()
