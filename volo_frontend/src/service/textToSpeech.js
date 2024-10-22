import { ElevenLabsClient, ElevenLabs } from "elevenlabs";

const ELEVENLABS_API_KEY = process.env.REACT_APP_ELEVENLABS_API_KEY;

if (!ELEVENLABS_API_KEY) {
  throw new Error("Missing ELEVENLABS_API_KEY in environment variables");
}

export const createAudioStreamFromText = async (text) => {
  const client = new ElevenLabsClient({apiKey: ELEVENLABS_API_KEY});
  await client.textToSpeech.convertAsStream("AZnzlk1XvdvUeBnXmlld", {
      optimize_streaming_latency: ElevenLabs.OptimizeStreamingLatency.Zero,
      output_format: ElevenLabs.OutputFormat.Mp32205032,
      text: text,
      voice_settings: {
          stability: 0.1,
          similarity_boost: 0.3,
          style: 0.2
      }
  });
};
