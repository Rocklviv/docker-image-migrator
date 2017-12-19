__version__ = "0.1.0"
"""
DIM - Python based CLI for Docker images migration from Docker Registry V1 to V2 or AWS ECR.
"""
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
        self._log("DEBUG", "Passed arguments to script: {}".format(self.current_time, self.args))
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
            resp = http.request("GET", "https://{}/v1/search".format(self.src_url))
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
            self._log("ERROR", "Error occured: {e}".format(e))

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
                # Creating repository in AWS ECR if needed.
                pass

            self._log("DEBUG", "Pulling image {src}/{image}:{tag}".format(
                src=self.src_url, image=image, tag=tag
            ))
            img = client.pull("{}/{}".format(self.src_url, image))
            if img:
                updated_image = client.tag("{}/{}".format(self.src_url, tag), "{}/{}".format(self.dest_url, image), tag=tag)
                if updated_image:
                    try:
                        client.push("{}/{}".format(self.dest_url, image), tag=tag)
                        client.remove_image("{}/{}:{}".format(self.src_url, image, tag))
                        client.remove_image("{}/{}:{}".format(self.dest_url, image, tag))
                        self._log("DEBUG", "Image {image} pushed to {dest} successfuly".format(
                            image=image, dest=self.dest_url
                        ))
                        self._log("DEBUG", "Images {src}/{image}:{tag} and {dest}/{image}:{tag} removed successfuly".format(
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
            print("[{:%Y-%m-%d %H:%M:%S}][ERROR] {}".format(self.current_time, e))
            raise

    @staticmethod
    def _log(type, msg):
        """
        Simple implementaiton of logging.
        :type: string Log level
        :msg: string Message to output
        """
        current_time = datetime.now()
        log_string = "[{:%Y-%m-%d %H:%M:%S}][{type}] {msg}".format(current_time, type=type, msg=msg)
        print(log_string)

if __name__ == "__main__":
    DIM()
