__version__ = "0.2.1"
"""
DIM - Python based CLI for Docker images migration from Docker Registry V1 to V2 or AWS ECR.
"""
import sys
import json
from argparse import ArgumentParser
from datetime import datetime
import urllib3


class DIM:

    IS_AWS_ECR = False
    DESCRIPTION = "DIM - Python based CLI for migration of Docker Images"

    def __init__(self):
        self.args = None
        # Private vars
        self.src_url = None
        self.dest_url = None
        self.image_list = []
        #
        self.parse_args()
        self.migrate()

    def parse_args(self):
        """
        Parsing CLI arguments passed to cli.
        """
        parser = ArgumentParser(description=self.DESCRIPTION)
        parser.add_argument("--src", required=True)
        parser.add_argument("--dest", required=True)
        parser.add_argument("--is-ecr", default=self.IS_AWS_ECR)
        self.args = parser.parse_args()
        self._log("DEBUG", "Passed arguments to script: {}".format(self.args))
        self._log("DEBUG", "Parsing arguments")
        self.src_url = self.args.src
        self.dest_url = self.args.dest
        self.IS_AWS_ECR = self.args.is_ecr

    def migrate(self):
        """
        Migration method executes pull docker image method.
        """
        self._get_images_list()

    # Private methods
    def _get_images_list(self):
        """
        Gets image list and runs Pull / Push method
        """
        http = urllib3.PoolManager()
        urllib3.disable_warnings()
        try:
            self._log("DEBUG", "Getting list of images")
            resp = http.request("GET", "https://{src}/v1/search".format(src=self.src_url))
            if resp.data:
                data = json.loads(resp.data.decode('utf-8'))
                for i in data.get('results'):
                    self.image_list.append(i.get('name').replace('library/', ''))
            
            # Looping over image list and storing all tags for each image list.
            for image in self.image_list:
                tags = self._get_image_tags(image)

                for tag, _hash in tags.items():
                    self._pull_push_image(image, tag)

        except Exception as e:
            self._log("ERROR", "Error occured: {error}".format(error=e))
            raise

    def _pull_push_image(self, image, tag):
        """
        Pull image from legacy repository. Creates new tag with new repository url and
        push to V2 repository or AWS ECR. Once image successfuly pushed to new repository 
        method will remove images with tag from local machine.
        TODO: Update method with failover mechanism.
        :image: string Image name.
        :tag: string Tag id to pull/push.
        :return: bool
        """
        try:
            from docker import Client, errors

            client = Client()
            if self.IS_AWS_ECR:
                self._create_ecr_repo(image)

            self._log("DEBUG", "Pulling image {src}/{image}:{tag}".format(
                src=self.src_url, image=image, tag=tag
            ))
            img = client.pull("{src}/{image}:{tag}".format(
                src=self.src_url, image=image, tag=tag
            ))
            if img:
                updated_image = client.tag("{src}/{image}".format(src=self.src_url, image=image), 
                                           "{dest}/{image}".format(dest=self.dest_url,
                                                                   image=image), tag)
                if updated_image:
                    try:
                        push_result = client.push("{dest}/{image}".format(dest=self.dest_url,
                                                                          image=image),
                                                  tag=tag, insecure_registry=True)
                        pr = self._check_docker_client_output(push_result)
                        for key in pr:
                            if key.get("error"):
                                self._log("ERROR", "Cannot push to registry: {error}".format(
                                            error=key.get("errorDetail")))
                                sys.exit(1)

                        client.remove_image("{src}/{image}:{tag}".format(
                            src=self.src_url, image=image, tag=tag))
                        client.remove_image("{dest}/{image}:{tag}".format(
                            dest=self.dest_url, image=image, tag=tag))
                        self._log("DEBUG", "Image {image} pushed to {dest} successfuly".format(
                            image=image, dest=self.dest_url
                        ))
                        self._log("DEBUG", "Images {src}/{image}:{tag} and {dest}/"
                                           "{image}:{tag} removed successfuly".format(
                            src=self.src_url, dest=self.dest_url, image=image, tag=tag
                        ))
                        return True
                    except errors.NotFound as e:
                        self._log("ERROR", "Error: {error}".format(error=e))
                        return False
        except ImportError as e:
            self._log("ERROR", "Cannot import module. {error}".format(error=e))
            raise

    def _get_image_tags(self, image):
        """
        Gets list of tags of image.
        :image: string Image name.
        :return: dict Dict with list of tags.
        """
        url = "https://{src}/v1/repositories/{image}/tags".format(src=self.src_url, image=image)
        try:
            http = urllib3.PoolManager()
            resp = http.request("GET", url)
            if resp.data:
                data = json.loads((resp.data).decode('utf-8'))
                return data
        except Exception as e:
            self._log("ERROR", "Error occured: {error}".format(error=e))
            raise

    def _create_ecr_repo(self, image):
        try:
            from python_terraform import Terraform
            terraform = Terraform()
            return_code, stdout, stderr = terraform.apply(var={"aws_ecr_name": image})
            print(return_code)

        except ImportError as e:
            self._log("ERROR", "Import occured: {error}".format(error=e))
            self._log("ERROR", "Try to install/reinstall python_terraform module.")
            raise

    # Static methods
    @staticmethod
    def _check_docker_client_output(output):
        """
        Checks docker client output on specific chars in response and returns list with dicts.
        :param output: string Docker client output.
        :return: list
        """
        updated_output = []
        if output:
            if type(output) == str:
                if "\r\n" in output:
                    tmp = output.split("\r\n")
                    for key in tmp:
                        if key != "":
                            updated_output.append(json.loads(key))
            return updated_output

    @staticmethod
    def _log(type, msg):
        """
        Simple implementaiton of logging.
        :type: string Log level
        :msg: string Message to output
        """
        try:
            from inspect import currentframe, getframeinfo

            current_time = datetime.now()
            current_frame = currentframe()
            log_string = "[{:%Y-%m-%d %H:%M:%S}][{type}][{lineno}] - {msg}".format(
                current_time, type=type, msg=msg, lineno=current_frame.f_back.f_lineno)
            print(log_string)
        except ImportError as e:
            print("[CRITICAL] Cannot import inspect module: {error}".format(error=e))
            raise

if __name__ == "__main__":
    DIM()
