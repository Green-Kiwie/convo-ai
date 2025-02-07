This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Getting Started

## Running Backend
First, create a virtual environment in the backend folder. 
Next, run "pip install -r requirements.txt"
create a .env file in the backend folder and add the following aws credentials: (AWS_ACCESS_KEY_ID=***, 
AWS_SECRET_ACCESS_KEY=***, 
AWS_REGION=us-east-2,
BEDROCK_MODEL=us.amazon.nova-lite-v1:0,
OPENAI_API_KEY=***)
To use the ngrok server, run "python -m fask_server"

## Running frontend
Remember to run backend before frontend.

If first time running, run "npm install --legacy-peer-deps"
First, run the development server:

after running the backend ngrok server, get the server url and replace it in the /src/app /page.js file. 

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.js`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.


to do:
1. remove openai aspects, convert to bedrock
2. instead of transferrring binary, transfer using s3
3. enable apis using lambda