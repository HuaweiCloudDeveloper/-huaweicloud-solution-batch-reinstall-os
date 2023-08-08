# coding: utf-8

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkecs.v2 import ReinstallServerWithCloudInitRequest, ReinstallServerWithCloudInitOption, ReinstallServerWithCloudInitRequestBody, ChangeServerOsWithCloudInitRequest, ChangeServerOsWithCloudInitRequestBody, ChangeServerOsWithCloudInitOption, EcsClient

import traceback


def handler(event, context):
    log = context.getLogger()
    result = check_configuration(context)
    if result is not None:
        return result

    processor = Processor(context)

    try:
        return processor.reinstall_change_os()
    except:
        log.error("failed to process image, "
                  f"exception：{traceback.format_exc()}")


def check_configuration(context):
    ak = context.getAccessKey().strip()
    sk = context.getSecretKey().strip()
    if not ak or not sk:
        ak = context.getUserData('ak', '').strip()
        sk = context.getUserData('sk', '').strip()
        if not ak or not sk:
            return 'ak or sk is empty'


class Processor:
    def __init__(self, context=None):
        self.log = context.getLogger()
        self.os_client = os_client(context)
        self.region = context.getUserData('region').strip()
        self.image_id = context.getUserData('image_id').strip()
        self.id_list = context.getUserData('ids').split()
        self.password_list = context.getUserData('passwords').split()

    def reinstall_os(self, idx, val):
        request = ReinstallServerWithCloudInitRequest()
        request.server_id = val
        osreinstallbody = ReinstallServerWithCloudInitOption(
            adminpass=self.password_list[idx],
            mode="withStopServer"
        )
        request.body = ReinstallServerWithCloudInitRequestBody(
            os_reinstall=osreinstallbody
        )
        response = self.os_client.reinstall_server_with_cloud_init(request)
        return response

    def change_os(self, idx, val):
        request = ChangeServerOsWithCloudInitRequest()
        request.server_id = val
        oschangebody = ChangeServerOsWithCloudInitOption(
            adminpass=self.password_list[idx],
            imageid=self.image_id,
            mode="withStopServer"
        )
        request.body = ChangeServerOsWithCloudInitRequestBody(
            os_change=oschangebody
        )
        response = self.os_client.change_server_os_with_cloud_init(request)
        return response

    def reinstall_change_os(self):
        try:
            response_list = []
            if self.image_id and self.image_id == "reinstall":
                for idx, val in enumerate(self.id_list):
                    response = self.reinstall_os(idx, val)
                    response_list.append(response)
            else:
                for idx, val in enumerate(self.id_list):
                    response = self.change_os(idx, val)
                    response_list.append(response)
            response_data = self.result_format_processing(response_list)
            return response_data
        except exceptions.ClientRequestException as e:
            self.log.error(f"failed to request reinstall change os"
                           f"status_code：{e.status_code}, "
                           f"request_id:{e.request_id}, "
                           f"error_code:{e.error_code}. "
                           f"error_msg:{e.error_msg}")
            return "Failed to bulk reinstall the operating system,Please check the log information"

    def result_format_processing(self, response):
        info = str(response)
        info_dict = {
            "success_msg": "Operating system reinstallation in batch succeeded",
            "statusCode": 200,
            "body": info
        }
        return info_dict


def os_client(context):
    ak = context.getAccessKey()
    sk = context.getSecretKey()
    credentials = BasicCredentials(ak, sk)
    client = EcsClient.new_builder() \
        .with_credentials(credentials) \
        .with_region(EcsRegion.value_of(context.getUserData('region'))) \
        .build()
    return client
