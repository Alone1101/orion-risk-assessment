import argparse, logging
from pathlib import Path
from orion.llm import OllamaProvider
from orion.submission import run_submission

def main() -> None:
    parser = argparse.ArgumentParser(description = "Run an ORION authorization risk assessment.")

    parser.add_argument("submission", type = Path, help = "Path to the application submission JSON file.")

    args = parser.parse_args()

    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s %(levelname)s %(name)s - %(message)s"
    )

    provider = OllamaProvider()

    result = run_submission(
        path = args.submission,
        provider = provider
    )

    print(result.model_dump_json(indent = 2))

if __name__ == "__main__":
    main()