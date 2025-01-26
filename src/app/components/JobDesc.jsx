import { useState } from "react";

import JobForm from "./JobForm";
import { TextField } from "@mui/material";

export default function JobDesc({ currentHTML, setCurrentHTML, jobLink, setJobLink, ...props }) {

    const [formOpened, setFormOpened] = useState(false);

    return (
        <div className="w-screen min-h-screen flex flex-col py-10 px-16 right-gradient">
            <nav className="flex">
            <button onClick={() => setCurrentHTML(1)} className="text-2xl hover:underline">⬅️ back</button>
            </nav>
            <h1 className="text-4xl my-16">first, let's talk about them!</h1>
            <div className="text-xl px-40 flex flex-col gap-y-4">
                <h1>enter your job post link:</h1>
                <TextField type='url' value={jobLink} onChange={(e) => setJobLink(e.target.value)} placeholder="ex. https://www.linkedin.com/jobs/view/1234"/>
                <h1 className="text-xl text-center my-10 underline">or</h1>
                <h1 className="text-xl">describe the job:</h1>
                <div onClick={() => setFormOpened(!formOpened)} className={formOpened ? "bg-white flex flex-row overflow-hidden items-center gap-x-10 cursor-pointer hover:bg-white p-4 rounded-md transition-all" : "flex flex-row overflow-hidden items-center gap-x-10 cursor-pointer hover:bg-white p-4 rounded-md transition-all"}>
                    <hr className="w-2/5 border-black" />
                    <h2 className="text-lg">{formOpened ? "Close the Form" : "Open the Form"}</h2>
                    <hr className="w-2/6 border-black"/>
                    {formOpened ? '⬆️' : '⬇️'}
                </div>

                {formOpened ? <JobForm {...props} /> : null}
                
            </div>   
            <button onClick={() => setCurrentHTML(3)} className="hover:bg-blue-950 text-center mx-auto my-8 mt-12 px-6 py-3 bg-blue-800 text-white rounded-3xl hover:bg-black-900 transition-all">next step!</button>
        </div>
    )
}