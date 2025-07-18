import os
from dropbox_sign import ApiClient, Configuration, apis, models
from dropbox_sign.rest import ApiException

def send_signature_request(api_key=None, signer_name="", signer_email="", pdf_path=""):
    if not api_key:
        api_key = os.getenv("DROPBOX_SIGN_API_KEY")

    if not api_key:
        raise ValueError("Dropbox Sign API key is not set.")
    
    print(f"Using API key: {api_key}")
    config = Configuration()
    config.username = api_key  # ✅ this is what Dropbox Sign expects


    with ApiClient(config) as api_client:
        signature_api = apis.SignatureRequestApi(api_client)

        signer = models.SubSignatureRequestSigner(
            email_address=signer_email,
            name=signer_name,
            order=0
        )

        try:
            with open(pdf_path, "rb") as pdf_file:
                request_data = models.SignatureRequestSendRequest(
                    title="Please sign your ticket",
                    subject="Sign your delivery ticket",
                    message="Please review and sign this document.",
                    signers=[signer],
                    files=[pdf_file],  # Pass open file, not path string
                    test_mode=True
                )

                response = signature_api.signature_request_send(request_data)
                return response.signature_request.signature_request_id
        except ApiException as e:
            return f"Error: {e}"
