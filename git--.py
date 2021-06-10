from rich import print
import argparse
import logging
import requests
import subprocess
import os

# configure the logger for global access
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def retrieve_tag_gitignore(*tags: str):
    """
    Given a number of tags retrieves the generated gitignore of the combined list
    :param tags: an arbitrary number of tags that .gitignore will recognize
    :return: the raw text response from the website
    """
    return requests.get(f"https://www.toptal.com/developers/gitignore/api/{','.join(tags)}").text


def create_gitignore(file_location: str, *tags: str):
    """
    Creates/Overwrites the existing gitignore to match the output of retrieve_tag_gitignore
    :param file_location: the location of the file (since the git repo might have been cloned elsewhere
    :param tags: an arbitrary number of tags that is passed to retrieve_tag_gitignore
    """
    with open(os.path.join(file_location, ".gitignore"), "w") as ignore_file:
        # open and re-write the gitignore
        logging.debug(f"Writing to file {os.path.join(file_location, '.gitignore')}")
        ignore_file.write(f"# .gitignore auto generated by https://github.com/CalvinSprouse/Git-- utilizing "
                          f"https://www.toptal.com/developers/gitignore\n# with user entered tags: {', '.join(tags)}\n"
                          f"### {os.path.basename(os.getcwd())} ###\n\n")
        ignore_file.write("\n".join(line for line in retrieve_tag_gitignore(*tags).split("\n")[3:]))


def clone_repo(url: str):
    """
    Calls subprocess.run with the provided url to git clone url
    :param url: the github repo to clone as in git clone [url]
    :return: True if it succeeded, None if there was an error
    """
    try:
        logging.debug(f"Cloning repo {url} to {os.getcwd()}")
        subprocess.run(f"git clone {url}", shell=True, check=True)
    except subprocess.CalledProcessError as clone_error:
        logging.error(clone_error)
        if clone_error.returncode == 128:
            print(f"{url} not valid repository")
        return None
    return True


if __name__ == "__main__":
    # create file handler (.log file)
    log_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs")
    log_file_name = "git--.log"
    try:
        # just in case log file doesnt exist, also log file should be with the .exe not wherever the repo is being made
        file = logging.FileHandler(os.path.join(log_location, log_file_name), mode="w+")
    except FileNotFoundError:
        # try it again cause we just made the file, if it fails its screwed
        os.mkdir(log_location)
        file = logging.FileHandler(os.path.join(log_location, log_file_name), mode="w+")
    file.setLevel(logging.INFO)
    file.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", datefmt="%H:%M:%S"))
    # create stream handler (cmd output)
    stream = logging.StreamHandler()
    stream.setLevel(logging.DEBUG)
    stream.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
    # add both stream and file handler to the logger (change stream level to warning for releases)
    logger.addHandler(file)
    logger.addHandler(stream)
    logger.info("Logger initialized")

    # create a parser to recognize the desired arguments
    parser = argparse.ArgumentParser(
        description="The superior single purpose version of git: git--. To initiate a repo type git-- init [url] ["
                    "list of tags for the project to construct a gitignore out of]")
    parser.add_argument("url", help="A url to the github repo like when calling git clone [url]")
    parser.add_argument("tags", nargs="*",
                        help="A list of tags for which git-- will plug into gitignore.io to get a .gitignore.")
    # get arguments from system
    args = vars(parser.parse_args())
    logger.debug(f"Received args: {args}")

    # validate tags to ensure they exist
    if clone_repo(args["url"]):
        create_gitignore(os.path.join(os.getcwd(), args["url"].split("/")[-1]), *args["tags"])
