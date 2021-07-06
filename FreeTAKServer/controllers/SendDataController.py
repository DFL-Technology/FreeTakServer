from FreeTAKServer.controllers.configuration.LoggingConstants import LoggingConstants
from FreeTAKServer.controllers.CreateLoggerController import CreateLoggerController
from typing import Union
loggingConstants = LoggingConstants()
logger = CreateLoggerController("SendDataController").getLogger()
import copy
#TODO: the part handling new connection from seperate process needs to be cleaned up

def get_callsigns(*, cot_object) -> list:
    callsigns = []
    if hasattr(cot_object.modelObject.detail, "marti") and hasattr(cot_object.modelObject.detail.marti, "dest"):
        for dest in cot_object.modelObject.detail.marti.dest:
            callsign = dest.getcallsign()
            if type(callsign) == str:
                callsigns.append(callsign)
            else:
                continue
    return callsigns

def get_uids(*, cot_object) -> list:
    """ get destination uids from an object

    gets destination uids specified in the chatgrp object within the model
    object and returns it as a list
    """
    uids = []
    if hasattr(cot_object.modelObject.detail, "_chat") and hasattr(cot_object.modelObject.detail._chat, "chatgrp"):
        uids.append(cot_object.modelObject.detail._chat.chatgrp.getuid1())
    return uids


def send_to_listener(*, listener, cot_string: bytes):
    if hasattr(listener, "socket"):
        listener.socket.send(cot_string)
    else:
        raise AttributeError("listener is missing attribute socket")


def verify_string_type(*, cot_string: Union[str, bytes]) -> bytes:
    if type(cot_string) == str:
        return cot_string.encode()
    elif type(cot_string) == bytes:
        return cot_string
    else:
        raise TypeError("cot_string must of type str or type bytes")


def send_to_share_pipe(*, cot_object, share_pipe) -> None:
    share_pipe.put(cot_object)


def send_to_all(*, listeners, cot_string: bytes) -> None:
    """send given bytes to all listeners in list

        iterates over listeners and sends cot_string to each one
        """
    for listener in listeners:
        send_to_listener(cot_string=cot_string, listener=listener)


def send_to_uids(*, listeners, cot_string: bytes, uids: list) -> None:
    """send given bytes to all listeners with uid in list

            iterates over listeners for listeners with a uid within the
            uid list. If found it will send the cot_string to the given
            listener
            """
    for listener in listeners:
        if listener.modelObject.uid in uids:
            send_to_listener(cot_string=cot_string, listener=listener)


def send_to_callsigns(*, listeners, cot_string: bytes, callsigns: list)->None:
    """send given bytes to all listeners with callsign in list

        iterates over listeners for listeners with a callsign within the
        callsign list. If found it will send the cot_string to the given
        listener
        """
    for listener in listeners:
        if listener.modelObject.detail.contact.callsign in callsigns:
            send_to_listener(cot_string=cot_string, listener=listener)


class SendDataController:

    def __init__(self):
        pass

    def send_data_in_queue(self, sender, processed_cot, client_information_queue, share_data_pipe = None) -> int:
        """Send data to all clients within a given list

        This method is used to parse and send data accordingly, to clients listed in clientInformationQueue parameter
        in addition to sending this data to the share_data_pipe

        Args:
            sender: unused
            processed_cot: a cot_object containing an xmlString attribute and modelObject attribute
            client_information_queue: a list of clientInformation objects each containing socket attributes
            share_data_pipe: Optional; if share_data_pipe is passed it should have the .put method and
                will be sent the cot_object

        Returns:
            None

        Raises:
            AttributeError: processedCoT argument must have xmlString attribute
            AttributeError: processedCoT argument must have modelObject attribute
        """
        try:
            uids = get_uids(cot_object=processed_cot)
            callsigns = get_callsigns(cot_object=processed_cot)
            if not hasattr(processed_cot, "modelObject"):
                raise AttributeError("processed_cot argument must have modelObject attribute")
            if hasattr(processed_cot, "xmlString"):
                cot_string = verify_string_type(cot_string=processed_cot.xmlString)
            elif hasattr(processed_cot, "idData"):
                cot_string = verify_string_type(cot_string=processed_cot.idData)
            else:
                raise AttributeError("processed_cot argument must have xmlString attribute")
            if uids:
                send_to_uids(cot_string=cot_string, listeners=client_information_queue, uids=uids)
            if callsigns:
                send_to_callsigns(cot_string=cot_string, listeners=client_information_queue, callsigns=callsigns)
            if not uids and not callsigns:
                send_to_all(cot_string=cot_string, listeners=client_information_queue)
            if share_data_pipe:
                send_to_share_pipe(cot_object=processed_cot, share_pipe=share_data_pipe)
            return 1
        except Exception as e:
            print(e)

