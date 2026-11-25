import { google } from '@ai-sdk/google';
import { generateText } from 'ai';

if (!process.env.GOOGLE_GENERATIVE_AI_API_KEY?.trim()) {
  throw new Error(
    'Add GOOGLE_GENERATIVE_AI_API_KEY to frontend/.env.local before running this example.',
  );
}

const { text } = await generateText({
  model: google('gemini-3.5-flash-lite'),
  prompt: 'Invent a new holiday and describe its traditions.',
});

console.log(text);
