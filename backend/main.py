import warnings
import functions_framework
import interview_api_gcp

@functions_framework.http
def gcp_init_interview_session(request):
    request_json = request.get_json(silent=True)

    website_url = request_json["website_url"]
    custom_job_str = request_json["custom_job_str"]
    interviewee_records = request_json["interviewee_records"]
    mode = request_json["mode"]
    session_key = request_json["session_key"]
    interviewee_resume = request_json["interviewee_resume"]

    return interview_api_gcp.init_interview_session(website_url, custom_job_str, interviewee_records, mode, session_key, interviewee_resume)



