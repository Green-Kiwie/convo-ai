import json
from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
from flask import Flask
from pyngrok import ngrok
import warnings
import boto3
import sys
import traceback
import base64
import time

from flask import request, jsonify
from flask_cors import CORS

from memory_class import local_chat_memory, combine_videos, get_mp4_binary
from crop_function import get_video_clips
from job_web_scrape import search_page
from resume_reader import extract_text_from_pdf




load_dotenv()
app = Flask(__name__)
CORS(app)

@app.route("/init_interview_session", methods=["POST"])
def init_interview_session() -> dict[str, int | str]:
    """flask api function to set up an interview question. returns the first question"""
    warnings.filterwarnings("ignore")

    data = request.get_json()

    website_url = data.get("website_url", "").strip()
    custom_job_str = str(data.get("custom_job_str", "")).strip()
    interviewee_records = str(data.get("interviewee_records")).strip()
    mode = data.get("mode", "").strip()
    session_key = data.get("session_key", "").strip()
    interviewee_resume = data.get("interviewee_resume", "")
    print(interviewee_resume)

    try:
        interviewee_resume_binary = bytes(interviewee_resume)
    except:
        interviewee_resume_binary = None
     
    if website_url:
        model_input = search_page(website_url)
    elif custom_job_str:
        model_input = custom_job_str
    else:
        raise ValueError("no website url or custom job str provided")
    
    print(model_input)

    try:
        interviewee_records += extract_text_from_pdf(interviewee_resume_binary)
        print(interviewee_records)

        bedrock_model = os.getenv("BEDROCK_MODEL")
        region = os.getenv('AWS_REGION')

        model_kwargs = { 
            "max_tokens_to_sample": 512,
            "temperature": 0.0,
        }

        llm = ChatBedrock(
            region_name = region,
            model_id=bedrock_model,
            model_kwargs=model_kwargs,
        )

        # Configure LangChain components
        prompt_template = """
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
        prompt = PromptTemplate.from_template(template=prompt_template)

        # Create LangChain pipeline
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser

        # Run the pipeline
        response = chain.invoke({"job_info": model_input, "interviewee_info": interviewee_records})

        chat_memory = local_chat_memory(session_key)
        chat_memory.reset_interview()
        chat_memory.store_interviewer_question(response)
        chat_memory.store_job_description(model_input)

        output = {
            "statusCode": 200,
            "body": json.dumps({"summary": response})
        }
        output = jsonify(output)
        output.headers.add("Access-Control-Allow-Origin", '*')

        # Return the result
        return output
    
    except Exception as e:
        # Handle errors and return meaningful messages
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

@app.route("/get_interview_question", methods=["POST"])
def get_interview_question():
    """Flask API function to get interview question based on user response. Returns the next question."""
    warnings.filterwarnings("ignore")

    data = request.get_json()
    print(data)
    
    video_input = data.get("user_input", "")#.encode("utf-8")  # Base64 encoded video data
    print(type(video_input))
    print(video_input[:5])
    session_key = data.get("session_key", "").strip()
    
    try:
        # Check if the video input is too large (80MB size limit, adjust as needed)
        if sys.getsizeof(video_input) > 1000*1000*1000:
            raise ValueError("File too big!")

        video_input = bytes(video_input)
        print(video_input)

        time_now = current_time_seconds = int(time.time())
        output_file_path = f'response_videos/output_video{time_now}.mp4'

        # Write the byte string to the file
        with open(output_file_path, 'wb') as f:
            f.write(video_input)


        client = boto3.client("bedrock-runtime", region_name="us-east-2")

        MODEL_ID = "us.amazon.nova-lite-v1:0"

        # Fetch chat history (assuming your implementation is correct)
        memory_obj = local_chat_memory(session_key)
        chat_history = memory_obj.get_chat_history()


        message_list = [
            {
                "role": "user",
                "content": [
                    {
                        "video": {
                            "format": "mp4",  # Specify the video format
                            "source": {"bytes": video_input},  # Send video as bytes
                        }
                    },
                    {"text": f"""You are an interviewer and you will be interviewing an applicant for a job.
                    Here is the previous chat history between you (the interviewer) and the interviewee: {chat_history}
                    You will also be provided with a video containing the latest response from the interviewee.

                    You are to end the interview at anytime you feel that a interview would end normally. 
                    That includes, but not limited to, encountering red flag responses from interviewees or you feel that you have an understanding of an interviewee.
                    You can end the interview by giving "****", that is four astrix in a row. 

                    You are to two give outputs, a transcript of the interviewee's response and your next question for the interviewee
                    You must output a JSON file with only two keys: 
                    1. "audio_transcript"
                    2. "next_question" 
                    """+
                    """Here is a template: 
                    {
                    "audio_transcript": "nice to meet you",
                    "next_question": "tell me about yourself"
                    }
                    Remember, as an interviewer, ask questions based on the job application and position the interviewee is applying for.
                """}
                ],
            }
        ] 

        response = client.converse(modelId=MODEL_ID, messages=message_list)

        #model_response = json.loads(response["body"].read())
        print(response['output']['message']['content'])
        print(response['output']['message']['content'][0])
        print(response['output']['message']['content'][0]['text'])
        print(json.loads(response['output']['message']['content'][0]['text']))
        next_question = json.loads(response['output']['message']['content'][0]['text'])['next_question']
        audio_transcript = json.loads(response['output']['message']['content'][0]['text'])['next_question']

        print(audio_transcript, next_question)


        
        memory_obj.store_interviewee_response(audio_transcript)  # Store the video input

        # Return the results as a JSON response
        output = {
            "statusCode": 200,
            "body": json.dumps({
                "audio_transcript": audio_transcript,
                "next_question": next_question
            })
        }
        output = jsonify(output)
        output.headers.add("Access-Control-Allow-Origin", '*')

        return output

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "traceback": traceback.format_exc()})
        }

@app.route("/get_video_analysis", methods=["POST"])
def get_video_analysis() -> dict[str, int | str]:
    """flask api function to get interview question based on user response. returns the next question"""
    warnings.filterwarnings("ignore")

    try:
        combine_videos("response_videos/")
        clip1_tuple, clip2_tuple, clip3_tuple, text_analysis = get_video_clips("main.mp4")

        clip1_binary = get_mp4_binary(clip1_tuple.directory_name)
        clip2_binary = get_mp4_binary(clip2_tuple.directory_name)
        clip3_binary = get_mp4_binary(clip3_tuple.directory_name)

        output = {
            "statusCode": 200,
            "body": json.dumps({
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
        }
        output = jsonify(output)
        output.headers.add("Access-Control-Allow-Origin", '*')

        # Return the result
        return output

    except Exception as e:
        # Handle errors and return meaningful messages
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "traceback": traceback.format_exc()})
        }
   

if __name__ == '__main__':
    public_url = ngrok.connect(5000)
    print(f"ngrok tunnel available at {public_url}")

    app.run(port=5000)
    
