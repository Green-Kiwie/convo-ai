import json
import os
# import boto3
# import sys
import traceback
# import time

from dotenv import load_dotenv
from flask import jsonify

# from langchain_aws import ChatBedrock
# from langchain.prompts import PromptTemplate
# from langchain_core.output_parsers import StrOutputParser

from modules.memory_class import LocalChatMemory, combine_videos, get_mp4_binary, S3ChatMemory
from modules.crop_function import get_video_clips
from modules.job_web_scrape import search_page
from modules.resume_reader import extract_text_from_pdf
import modules.s3_interactor as s3_interactor

from google import genai
from google.genai.types import HttpOptions, Part

load_dotenv()

def _get_init_prompt_template(job_info, interviewee_info):
    return f"""
                            You are a interviewer and you will be interviewing an applicant for a job. The job information is either given as a website or a string with the job description. 
                            If you are given a website, use the website scraping tool to retrieve the information from the website. 
                            If you are given a string with the job description, you are to take the job description as the sole source of truth for the interview. 
                            Assume nothing about the interviewee unless the information is provided to you. 

                            As an interviewer, you are to provide one starting question to the interviewee based on what the interviewee has mentioned previously. 
                            Return exactly what you would give in your first question, nothing else. 

                            You are to end the interview at anytime you feel that a interview would end normally. 
                            That includes, but not limited to, encountering red flag responses from interviewees or you feel that you have an understanding of an interviewee.
                            You can end the interview by giving "****", that is four astrix in a row. 
                            

                            Here is the job information: {job_info}
                            Here is some information about the interviewee you may reference: {interviewee_info}

                            Remember that you are the interviewer and that you are supposed to provide question. 
                          """

def _get_next_question_prompt_template(chat_history): 
    return f"""You are an interviewer and you will be interviewing an applicant for a job.
                    Here is the previous chat history between you (the interviewer) and the interviewee: {chat_history}
                    You will also be provided with a video containing the latest response from the interviewee.

                    You are to end the interview at anytime you feel that a interview would end normally. 
                    That includes, but not limited to, encountering red flag responses from interviewees or you feel that you have an understanding of an interviewee. 

                    You are to two give outputs, a transcript of the interviewee's response and your next question for the interviewee
                    The output must start with the round brackets and end with the round brackets. 
                    You must output a JSON file with only two keys: 
                    1. "audio_transcript"
                    2. "next_question" 
                    """+"""Here is a template (starting after and ending before the "***'): 
                    ***{
                    "audio_transcript": "nice to meet you",
                    "next_question": "tell me about yourself"
                    }***
                    Remember, as an interviewer, ask questions based on the job application and position the interviewee is applying for.
                """

# def _get_next_question_prompt_template_s3(bucket: str, video_file_name: str, chat_history):
#     return [
#                 {
#                     "role": "user",
#                     "content": [
#                         # {
#                         #     "video": {
#                         #         "format": "mp4",
#                         #         "source": {
#                         #             "s3Location": {
#                         #                 "uri": "s3://convo-ai-io/test/WIN_20250206_17_47_02_Pro.mp4", 
#                         #                 "bucketOwner": "597088029429"
#                         #             }
#                         #         }
#                         #     }
#                         # },
#                         {
#                             "text": "Provide video titles for this clip."
#                         }
#                     ]
#                 }
#             ]



def _get_job_data(website_url: str, custom_job_str: str) -> str:
    """returns the job data as a string based on both url and input job string"""
    if website_url:
        model_input = search_page(website_url)
    elif custom_job_str:
        model_input = custom_job_str
    else:
        raise ValueError("no website url or custom job str provided")
    
    return model_input

def _parse_resume(interviewee_resume: bytearray) -> str:
    """returns the resuem in bytes"""
    try:
        interviewee_resume_binary = bytes(interviewee_resume)
    except:
        interviewee_resume_binary = None

    interviewee_resume = extract_text_from_pdf(interviewee_resume_binary)
    return interviewee_resume

def _create_success_output(kwargs) -> "jsonify":
    output = {
        "statusCode": 200,
        "body": json.dumps(kwargs)
    }
    output = jsonify(output)

    return output

def _create_fail_output(error: "error") -> 'jsonify':
    stack_trace = traceback.format_exc()
    print(stack_trace)
    return {
            "statusCode": 500,
            "body": json.dumps({"error": str(error)}),
            "location": stack_trace
        } 

def _get_gemini_response(prompt: str, input_file_uri = None) -> str:
    """gets the gemini response to a given prompt"""
    if input_file_uri == None:
        input_contents = [prompt]
    else:
        input_contents=[
            Part.from_uri(
                file_uri=input_file_uri,
                mime_type="video/mp4",
            ),
            prompt,
        ],
    
    client = genai.Client(http_options=HttpOptions(api_version="v1"))
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=input_contents,
    )
    return response.text

def _parse_gemini_response_into_json(response: str) -> dict:
    """find the open and closing curly brackets and converts json to string"""
    try:
        start = response.find("{")
        end = response.rfind("}") + 1  # Include the last closing brace

        if start == -1 or end == 0:
            raise ValueError("No valid JSON object found in response")

        json_str = response[start:end]
        return json.loads(json_str) 

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid model response: {e}")
    
def init_interview_session(website_url: str, custom_job_str: str, interviewee_records: str,
                           
                           mode: str, session_key: str, interviewee_resume: bytearray) -> dict[str, int | str]:
    
    interviewee_records += _parse_resume(interviewee_resume)
    model_input = _get_job_data(website_url, custom_job_str)
    
    print(interviewee_records)
    print(model_input)

    try:
        prompt = _get_init_prompt_template(job_info = model_input, interviewee_info = interviewee_records)
        response = _get_gemini_response(prompt)
        
        chat_memory = LocalChatMemory(session_key)
        chat_memory.reset_interview()
        chat_memory.store_job_description(model_input)
        chat_memory.store_interviewer_question(response)

        output = _create_success_output({"summary": response})
        return output
    
    except Exception as e:
        return _create_fail_output(e)
    
def get_interview_question(video_uri: str, session_key: str):
    try:
        memory_obj = LocalChatMemory(session_key)
        chat_history = memory_obj.get_chat_history()
        
        prompt = _get_next_question_prompt_template(chat_history)
        gemini_response = _get_gemini_response(prompt, video_uri)
        response_json = _parse_gemini_response_into_json(gemini_response)

        audio_transcript, next_question = response_json["audio_transcript"], response_json["next_question"] 
        memory_obj.store_interviewee_response(audio_transcript)  
        print(chat_history)

        output = _create_success_output({
                "audio_transcript": audio_transcript,
                "next_question": next_question
            })
        return output

    except Exception as e:
        return _create_fail_output(e)

def get_video_analysis():
    try:
        main_video_path = combine_videos("response_videos/")
        clip1_tuple, clip2_tuple, clip3_tuple, text_analysis = get_video_clips(main_video_path)

        clip1_binary = get_mp4_binary(clip1_tuple.directory_name)
        clip2_binary = get_mp4_binary(clip2_tuple.directory_name)
        clip3_binary = get_mp4_binary(clip3_tuple.directory_name)

        output = _create_success_output({
                "text_report": text_analysis,
                "video1": clip1_binary,
                "video2": clip2_binary,
                "video3": clip3_binary,
                "video1_title": clip1_tuple.event_title, 
                "video2_title": clip2_tuple.event_title,
                "video3_title": clip3_tuple.event_title,
                "video1_feedback": clip1_tuple.event_feedback,
                "video2_feedback": clip2_tuple.event_feedback,
                "video3_feedback": clip3_tuple.event_feedback
            })
        return output

    except Exception as e:
        return _create_fail_output(e)
   

def get_s3_details(session_key: str):
    """creates a directory based on the session key and returns path to directory"""
    try:
        bucket = os.getenv("IO_BUCKET")
        directory = session_key + "/"
        s3_interactor.create_directory(bucket, directory)

        output = _create_success_output({
                "bucket": bucket,
                "key": directory
            })
        return output
    
    except Exception as e:
        return _create_fail_output(e)

# def init_interview_session_s3(website_url: str, custom_job_str: str, interviewee_records: str,
#                            mode: str, session_directory: str, resume_file_path: str):
    
#     try:
#         bucket = os.getenv("IO_BUCKET")
#         resume_byte = s3_interactor.read_pdf(bucket, resume_file_path)
#         interviewee_records = extract_text_from_pdf(resume_byte)

#         model_input = _get_job_data(website_url, custom_job_str)

#         prompt_template = _get_init_prompt_template()
#         prompt = PromptTemplate.from_template(template=prompt_template)

#         chain = setup_langchain(prompt)
#         response = invoke_chain(chain, {"job_info": model_input, "interviewee_info": interviewee_records})
        
#         chat_memory = S3ChatMemory(bucket, session_directory)
#         chat_memory.reset_interview()
#         chat_memory.store_job_description(model_input)
#         chat_memory.store_interviewer_question(response)

#         output = _create_success_output({"summary": response})
#         return output
#     except Exception as e:
#         return _create_fail_output(e)

# def get_interview_question_s3(session_directory: str, video_directory: str):
#     try:
#         bucket = os.getenv("IO_BUCKET")
#         memory_obj = S3ChatMemory(bucket, session_directory)
#         chat_history = memory_obj.get_chat_history()

#         message_list = _get_next_question_prompt_template_s3(bucket, video_directory, chat_history)
#         print(message_list)

#         audio_transcript, next_question = get_bedrock_response(message_list)
#         memory_obj.store_interviewee_response(audio_transcript)  
#         print(chat_history)
        
#         output = _create_success_output({
#                     "audio_transcript": audio_transcript,
#                     "next_question": next_question
#                 })
#         return output
    
#     except Exception as e:
#         return _create_fail_output(e)


if __name__ == "__main__":
    
    # client = genai.Client(http_options=HttpOptions(api_version="v1"))
    # response = client.models.generate_content(
    #     model="gemini-2.0-flash-001",
    #     contents=[
    #         Part.from_uri(
    #             file_uri="gs://convo_development/main.mp4",
    #             mime_type="video/mp4",
    #         ),
    #         "Provide video titles for this clip.",
    #     ],
    # )
    # print(response.text)


    prompt = _get_next_question_prompt_template(chat_history = None)
    gemini_response = _get_gemini_response(prompt, "gs://convo_development/main.mp4")
    print(gemini_response)