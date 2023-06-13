from datetime import datetime
from typing import Any, Dict, Optional
from omegaconf import OmegaConf
from pathlib import Path
import pandas as pd
import requests
import logging
import json

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("dana-client")


def add_new_optimum_build(
    project_id: str,
    build_id: int,
    dashboard_url: str,
    bearer_token: str,
    override: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """
    Posts a new build to the dashboard.
    """

    build_url = f"{dashboard_url}/apis/addBuild"

    build_payload = {
        "projectId": project_id,
        "build": {
            "buildId": build_id,
            "infos": {
                "hash": "commit_hash",  # TODO: get commit hash
                "abbrevHash": "commit_abbrev_hash",  # TODO: get commit abbrev hash
                "authorName": "ilyas",
                "authorEmail": "ilyas@gmail.com",
                "subject": "commit_subject",  # TODO: get commit subject
                "url": "commit_url",  # TODO: get commit url
            },
        },
        "override": override,
    }

    post_to_dashboard(
        dashboard_url=build_url,
        bearer_token=bearer_token,
        payload=build_payload,
        dry_run=dry_run,
        verbose=verbose,
    )


def add_new_optimum_series(
    project_id: str,
    series_id: str,
    dashboard_url: str,
    bearer_token: str,
    series_description: Optional[str] = None,
    override: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    average_range: int = 5,
    average_min_count: int = 3,
    better_criterion: str = "lower",
) -> None:
    """
    Posts a new series to the dashboard.
    """

    series_url = f"{dashboard_url}/apis/addSerie"
    series_payload = {
        "projectId": project_id,
        "serieId": series_id,
        "analyse": {
            "benchmark": {
                "range": average_range,
                "required": average_min_count,
                "trend": better_criterion,
            }
        },
        "override": override,
    }

    if series_description is not None:
        series_payload["description"] = series_description

    post_to_dashboard(
        dashboard_url=series_url,
        bearer_token=bearer_token,
        payload=series_payload,
        dry_run=dry_run,
        verbose=verbose,
    )


def add_new_sample(
    project_id: str,
    series_id: str,
    build_id: int,
    sample_value: int,
    dashboard_url: str,
    bearer_token: str,
    override: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """
    Posts a new sample to the dashboard.
    """
    sample_url = f"{dashboard_url}/apis/addSample"

    sample_payload = {
        "projectId": project_id,
        "serieId": series_id,
        "sample": {"buildId": build_id, "value": sample_value},
        "override": override,
    }

    post_to_dashboard(
        dashboard_url=sample_url,
        bearer_token=bearer_token,
        payload=sample_payload,
        dry_run=dry_run,
        verbose=verbose,
    )


def post_to_dashboard(
    dashboard_url: str,
    bearer_token: str,
    payload: Dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    data = json.dumps(payload)

    if dry_run or verbose:
        print(f"API request payload: {data}")

    if dry_run:
        return

    response = requests.post(
        dashboard_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
        },
    )
    code = response.status_code
    LOGGER.info(f"API response code: {code}")


def main():
    # The URL of the dashboard (for now, it's local)
    DASHBOARD_URL = "http://localhost:7000"

    # The bearer token to use for authentication
    BEARER_TOKEN = open("token.txt").read().strip()

    # set to tru to ovverride existing series
    OVERRIDE = True

    DRY_RUN = False
    VERBOSE = False

    for project_folder in Path("dana").iterdir():
        project_id = project_folder.name

        LOGGER.info(f" + Processing project {project_id}...")
        for series_foler in project_folder.iterdir():
            series_id = series_foler.name
            # a series is a benchmark on which we want to track the performance

            LOGGER.info(f"\t + Processing series {series_id}...")
            config = OmegaConf.load(list(series_foler.glob("*/hydra_config.yaml"))[0])
            series_description = OmegaConf.to_yaml(config)

            add_new_optimum_series(
                project_id=project_id,
                series_id=series_id,
                dashboard_url=DASHBOARD_URL,
                bearer_token=BEARER_TOKEN,
                series_description=series_description,
                override=OVERRIDE,
                dry_run=DRY_RUN,
                verbose=VERBOSE,
            )

            for build_folder in series_foler.iterdir():
                # build folder name is a datetime %Y%m%d-%H%M%S that we convert it to an int
                build_id = int(
                    datetime.strptime(build_folder.name, "%Y%m%d-%H%M%S").timestamp()
                )
                # a build is an event or time point that marks one measurement of the series
                # the same build id can be used for multiple series (a release, a commit or a PR)

                LOGGER.info(f"\t\t + Processing buld {build_id}...")
                add_new_optimum_build(
                    project_id=project_id,
                    build_id=build_id,
                    series_id=series_id,
                    dashboard_url=DASHBOARD_URL,
                    bearer_token=BEARER_TOKEN,
                    override=OVERRIDE,
                    dry_run=DRY_RUN,
                    verbose=VERBOSE,
                )

                # inference_results.csv contains one row
                inference_results = pd.read_csv(
                    build_folder / "inference_results.csv"
                ).to_dict("records")[0]

                # convert to ms (what dana expects)
                sample_value = inference_results["Model latency mean (s)"] * 1000

                # a sample is a measurement of a series at a given build
                LOGGER.info(f"\t\t + Adding new sample...")
                add_new_sample(
                    project_id=project_id,
                    series_id=series_id,
                    build_id=build_id,
                    sample_value=sample_value,
                    dashboard_url=DASHBOARD_URL,
                    bearer_token=BEARER_TOKEN,
                    override=OVERRIDE,
                    dry_run=DRY_RUN,
                    verbose=VERBOSE,
                )


if __name__ == "__main__":
    main()
