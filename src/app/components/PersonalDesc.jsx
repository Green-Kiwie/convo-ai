import { useState } from "react"

import PersonalForm from "./PersonalForm";

export default function PersonalDesc({ currentHTML, setCurrentHTML, resumeName, setResume, setResumeFile, ...props }) {

    const [formOpened, setFormOpened] = useState(false);
    
    function handleFileChange(event) {
        console.log('call changed')
        const selectedFile = event.target.files[0]

        const reader = new FileReader()
        reader.onload = (event) => {
            const arrayBuffer = event.target.result;
            const byteArray = new Uint8Array(arrayBuffer);
            const bytes = Array.from(byteArray);
            setResumeFile(bytes)
            console.log(bytes)
        }
        reader.readAsArrayBuffer(selectedFile)
        setResume(selectedFile.name)
    }

    return (
        <div className="w-screen min-h-screen flex flex-col py-10 px-16 right-gradient">
            <nav className="flex">
            <button onClick={() => setCurrentHTML(2)} className="text-2xl hover:underline">⬅️ back</button>
            </nav>
            <h1 className="text-4xl my-16">next, let's talk about you!</h1>
            <div className="text-xl px-40 flex flex-col gap-y-4">

                <div className="flex flex-row justify-between bg-white px-10 py-4 rounded-lg items-center">
                    <h1>import resume</h1>
                    <div className="flex flex-row gap-x-4 items-center">
                        <p className="text-sm text-gray-400 underline">{resumeName}</p>
                        <label htmlFor="resume-upload" className="cursor-pointer flex flex-row items-center gap-x-2 bg-blue-800 hover:bg-blue-950 transition-all text-white p-2 rounded-lg">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.941-7.81 7.81a1.5 1.5 0 0 0 2.112 2.13" />
                            </svg>
                            Attach File
                        </label>
                        <input onChange={handleFileChange} type="file" accept="application/pdf" id='resume-upload' />
                    </div>
                </div>

                <h1 className="text-xl text-center my-10 underline">or</h1>

                <h1 className="text-xl">describe yourself:</h1>
    
                <div onClick={() => setFormOpened(!formOpened)} className={formOpened ? "bg-white flex flex-row overflow-hidden items-center gap-x-10 cursor-pointer hover:bg-white p-4 rounded-md transition-all" : "flex flex-row overflow-hidden items-center gap-x-10 cursor-pointer hover:bg-white p-4 rounded-md transition-all"}>
                    <hr className="w-2/5 border-black" />
                    <h2 className="text-lg">{formOpened ? "Close the Form" : "Open the Form"}</h2>
                    <hr className="w-2/6 border-black"/>
                    {formOpened ? '⬆️' : '⬇️'}
                </div>

                { formOpened ? <PersonalForm {...props} /> : null }    
                
            </div>   
            <button onClick={() => setCurrentHTML(4)} className="hover:bg-blue-950 text-center mx-auto my-8 mt-12 px-6 py-3 bg-blue-800 text-white rounded-3xl hover:bg-black-900 transition-all">next step!</button>
        </div>
    )
}