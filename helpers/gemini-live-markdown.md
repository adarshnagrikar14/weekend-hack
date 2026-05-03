The Live API enables low-latency, real-time voice and vision interactions with
Gemini. It processes continuous streams of audio, images, and text to deliver
immediate, human-like spoken responses, creating a natural conversational
experience for your users.

![Live API Overview](https://ai.google.dev/static/gemini-api/docs/images/live-api-overview.png)
[Try the Live API in Google AI Studio](https://aistudio.google.com/live) [Clone example apps from GitHub](https://github.com/google-gemini/gemini-live-api-examples) [Use coding agent skills](https://ai.google.dev/gemini-api/docs/coding-agents)

## Use cases

Live API can be used to build real-time voice agents for a
variety of industries, including:

- **E-commerce and retail:** Shopping assistants that offer personalized recommendations and support agents that resolve customer issues.
- **Gaming:** Interactive non-player characters (NPCs), in-game help assistants, and real-time translation of in-game content.
- **Next-gen interfaces:** Voice- and video-enabled experiences in robotics, smart glasses, and vehicles.
- **Healthcare:** Health companions for patient support and education.
- **Financial services:** AI advisors for wealth management and investment guidance.
- **Education:** AI mentors and learner companions that provide personalized instruction and feedback.

## Key features

Live API offers a comprehensive set of features for building
robust voice agents:

- [**Multilingual support**](https://ai.google.dev/gemini-api/docs/live-guide#supported-languages): Converse in 70 supported languages.
- [**Barge-in**](https://ai.google.dev/gemini-api/docs/live-guide#interruptions): Users can interrupt the model at any time for responsive interactions.
- [**Tool use**](https://ai.google.dev/gemini-api/docs/live-tools): Integrates tools like function calling and Google Search for dynamic interactions.
- [**Audio transcriptions**](https://ai.google.dev/gemini-api/docs/live-guide#audio-transcription): Provides text transcripts of both user input and model output.
- [**Proactive audio**](https://ai.google.dev/gemini-api/docs/live-guide#proactive-audio): Lets you control when the model responds and in what contexts.
- [**Affective dialog**](https://ai.google.dev/gemini-api/docs/live-guide#affective-dialog): Adapts response style and tone to match the user's input expression.

## Technical specifications

The following table outlines the technical specifications for the
Live API:

| Category | Details |
|---|---|
| Input modalities | Audio (raw 16-bit PCM audio, 16kHz, little-endian), images (JPEG \<= 1FPS), text |
| Output modalities | Audio (raw 16-bit PCM audio, 24kHz, little-endian) |
| Protocol | Stateful WebSocket connection (WSS) |

## Choose an implementation approach

When integrating with Live API, you'll need to choose one of the following
implementation approaches:

- **Server-to-server** : Your backend connects to the Live API using [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API). Typically, your client sends stream data (audio, video, text) to your server, which then forwards it to the Live API.
- **Client-to-server** : Your frontend code connects directly to the Live API using [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) to stream data, bypassing your backend.

> [!NOTE]
> **Note:** Client-to-server generally offers better performance for streaming audio and video, since it bypasses the need to send the stream to your backend first. It's also easier to set up since you don't need to implement a proxy that sends data from your client to your server and then your server to the API. However, for production environments, in order to mitigate security risks, we recommend using [ephemeral tokens](https://ai.google.dev/gemini-api/docs/ephemeral-tokens) instead of standard API keys.

## Get started

Select the guide that matches your development environment:
Server-to-server

### [GenAI SDK tutorial](https://ai.google.dev/gemini-api/docs/live-api/get-started-sdk)


Connect to the Gemini Live API using the GenAI SDK to build a real-time multimodal application with a Python backend.

Client-to-server

### [WebSocket tutorial](https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket)


Connect to the Gemini Live API using WebSockets to build a real-time multimodal application with a JavaScript frontend and ephemeral tokens.

Agent development kit

### [ADK tutorial](https://google.github.io/adk-docs/streaming/)


Create an agent and use the Agent Development Kit (ADK) Streaming to enable voice and video communication.

## Partner integrations


To streamline the development of real-time audio and video apps, you can use
a third-party integration that supports the Gemini Live
API over WebRTC or WebSockets.
[LiveKit
Use the Gemini Live API with LiveKit Agents.](https://docs.livekit.io/agents/models/realtime/plugins/gemini/) [Pipecat by Daily
Create a real-time AI chatbot using Gemini Live and Pipecat.](https://docs.pipecat.ai/guides/features/gemini-live) [Fishjam by Software Mansion
Create live video and audio streaming applications with Fishjam.](https://docs.fishjam.io/tutorials/gemini-live-integration) [Vision Agents by Stream
Build real-time voice and video AI applications with Vision Agents.](https://visionagents.ai/integrations/gemini) [Voximplant
Connect inbound and outbound calls to Live API with Voximplant.](https://voximplant.com/products/gemini-client) [Agora
Build real-time conversational AI applications with Agora.](https://docs.agora.io/en/conversational-ai/models/mllm/gemini) [Firebase AI SDK
Get started with the Gemini Live API using Firebase AI Logic.](https://firebase.google.com/docs/ai-logic/live-api?api=dev)

--

The Gemini Live API allows for real-time, bidirectional interaction with Gemini models, supporting audio, video, and text inputs and native audio outputs. This guide explains how to integrate with the API using the Google GenAI SDK on your server.
[Try the Live API in Google AI Studio](https://aistudio.google.com/live) [Clone the example app from GitHub](https://github.com/google-gemini/gemini-live-api-examples/tree/main/gemini-live-genai-python-sdk) [Use coding agent skills](https://ai.google.dev/gemini-api/docs/coding-agents)

## Overview

The Gemini Live API uses WebSockets for real-time communication. The `google-genai` SDK provides a high-level asynchronous interface for managing these connections.

Key concepts:

- **Session**: A persistent connection to the model.
- **Config**: Setting up modalities (audio/text), voice, and system instructions.
- **Real-time Input**: Sending audio and video frames as blobs.

## Connecting to the Live API

Start a Live API session with an API key:

### Python

    import asyncio
    from google import genai

    client = genai.Client(api_key="YOUR_API_KEY")

    model = "gemini-3.1-flash-live-preview"
    config = {"response_modalities": ["AUDIO"]}

    async def main():
        async with client.aio.live.connect(model=model, config=config) as session:
            print("Session started")
            # Send content...

    if __name__ == "__main__":
        asyncio.run(main())

### JavaScript

    import { GoogleGenAI, Modality } from '@google/genai';

    const ai = new GoogleGenAI({ apiKey: "YOUR_API_KEY"});
    const model = 'gemini-3.1-flash-live-preview';
    const config = { responseModalities: [Modality.AUDIO] };

    async function main() {

      const session = await ai.live.connect({
        model: model,
        callbacks: {
          onopen: function () {
            console.debug('Opened');
          },
          onmessage: function (message) {
            console.debug(message);
          },
          onerror: function (e) {
            console.debug('Error:', e.message);
          },
          onclose: function (e) {
            console.debug('Close:', e.reason);
          },
        },
        config: config,
      });

      console.debug("Session started");
      // Send content...

      session.close();
    }

    main();

## Sending text

Text can be sent using `send_realtime_input` (Python) or `sendRealtimeInput` (JavaScript).

### Python

    await session.send_realtime_input(text="Hello, how are you?")

### JavaScript

    session.sendRealtimeInput({
      text: 'Hello, how are you?'
    });

## Sending audio

Audio needs to be sent as raw PCM data (raw 16-bit PCM audio, 16kHz, little-endian).

### Python

    # Assuming 'chunk' is your raw PCM audio bytes
    await session.send_realtime_input(
        audio=types.Blob(
            data=chunk,
            mime_type="audio/pcm;rate=16000"
        )
    )

### JavaScript

    // Assuming 'chunk' is a Buffer of raw PCM audio
    session.sendRealtimeInput({
      audio: {
        data: chunk.toString('base64'),
        mimeType: 'audio/pcm;rate=16000'
      }
    });

For an example of how to get the audio from the client device (e.g. the browser)
see the end-to-end example on [GitHub](https://github.com/google-gemini/gemini-live-api-examples/blob/main/gemini-live-genai-python-sdk/frontend/media-handler.js#L31-L70).

## Sending video

Video frames are sent as individual images (e.g., JPEG or PNG) at a specific frame rate (max 1 frame per second).

### Python

    # Assuming 'frame' is your JPEG-encoded image bytes
    await session.send_realtime_input(
        video=types.Blob(
            data=frame,
            mime_type="image/jpeg"
        )
    )

### JavaScript

    // Assuming 'frame' is a Buffer of JPEG-encoded image data
    session.sendRealtimeInput({
      video: {
        data: frame.toString('base64'),
        mimeType: 'image/jpeg'
      }
    });

For an example of how to get the video from the client device (e.g. the browser)
see the end-to-end example on [GitHub](https://github.com/google-gemini/gemini-live-api-examples/blob/main/gemini-live-genai-python-sdk/frontend/media-handler.js#L84-L120).

## Receiving audio

The model's audio responses are received as chunks of data.

### Python

    async for response in session.receive():
        if response.server_content and response.server_content.model_turn:
            for part in response.server_content.model_turn.parts:
                if part.inline_data:
                    audio_data = part.inline_data.data
                    # Process or play the audio data

### JavaScript

    // Inside the onmessage callback
    const content = response.serverContent;
    if (content?.modelTurn?.parts) {
      for (const part of content.modelTurn.parts) {
        if (part.inlineData) {
          const audioData = part.inlineData.data;
          // Process or play audioData (base64 encoded string)
        }
      }
    }

See the example app on GitHub to learn how to [receive the audio on your server](https://github.com/google-gemini/gemini-live-api-examples/blob/main/gemini-live-genai-python-sdk/gemini_live.py#L86-L98) and [play it in the browser](https://github.com/google-gemini/gemini-live-api-examples/blob/main/gemini-live-genai-python-sdk/frontend/media-handler.js#L145-L174).

## Receiving text

Transcriptions for both user input and model output are available in the server content.

### Python

    async for response in session.receive():
        content = response.server_content
        if content:
            if content.input_transcription:
                print(f"User: {content.input_transcription.text}")
            if content.output_transcription:
                print(f"Gemini: {content.output_transcription.text}")

### JavaScript

    // Inside the onmessage callback
    const content = response.serverContent;
    if (content?.inputTranscription) {
      console.log('User:', content.inputTranscription.text);
    }
    if (content?.outputTranscription) {
      console.log('Gemini:', content.outputTranscription.text);
    }

## Handling tool calls

The API supports tool calling (function calling). When the model requests a tool call, you must execute the function and send the response back.

### Python

    async for response in session.receive():
        if response.tool_call:
            function_responses = []
            for fc in response.tool_call.function_calls:
                # 1. Execute the function locally
                result = my_tool_function(**fc.args)

                # 2. Prepare the response
                function_responses.append(types.FunctionResponse(
                    name=fc.name,
                    id=fc.id,
                    response={"result": result}
                ))

            # 3. Send the tool response back to the session
            await session.send_tool_response(function_responses=function_responses)

### JavaScript

    // Inside the onmessage callback
    if (response.toolCall) {
      const functionResponses = [];
      for (const fc of response.toolCall.functionCalls) {
        const result = myToolFunction(fc.args);
        functionResponses.push({
          name: fc.name,
          id: fc.id,
          response: { result }
        });
      }
      session.sendToolResponse({ functionResponses });
    }

## What's next

- Read the full Live API [Capabilities](https://ai.google.dev/gemini-api/docs/live-guide) guide for key capabilities and configurations; including Voice Activity Detection and native audio features.
- Read the [Tool use](https://ai.google.dev/gemini-api/docs/live-tools) guide to learn how to integrate Live API with tools and function calling.
- Read the [Session management](https://ai.google.dev/gemini-api/docs/live-session) guide for managing long running conversations.
- Read the [Ephemeral tokens](https://ai.google.dev/gemini-api/docs/ephemeral-tokens) guide for secure authentication in [client-to-server](https://ai.google.dev/gemini-api/docs/live-api/get-started-sdk#implementation-approach) applications.
- For more information about the underlying WebSockets API, see the [WebSockets API reference](https://ai.google.dev/api/live).

--

The Gemini Live API allows for real-time, bidirectional interaction with Gemini models, supporting audio, video, and text inputs and native audio outputs. This guide explains how to integrate with the API using the Google GenAI SDK on your server.
[Try the Live API in Google AI Studio](https://aistudio.google.com/live) [Clone the example app from GitHub](https://github.com/google-gemini/gemini-live-api-examples/tree/main/gemini-live-genai-python-sdk) [Use coding agent skills](https://ai.google.dev/gemini-api/docs/coding-agents)

## Overview

The Gemini Live API uses WebSockets for real-time communication. The `google-genai` SDK provides a high-level asynchronous interface for managing these connections.

Key concepts:

- **Session**: A persistent connection to the model.
- **Config**: Setting up modalities (audio/text), voice, and system instructions.
- **Real-time Input**: Sending audio and video frames as blobs.

## Connecting to the Live API

Start a Live API session with an API key:

### Python

    import asyncio
    from google import genai

    client = genai.Client(api_key="YOUR_API_KEY")

    model = "gemini-3.1-flash-live-preview"
    config = {"response_modalities": ["AUDIO"]}

    async def main():
        async with client.aio.live.connect(model=model, config=config) as session:
            print("Session started")
            # Send content...

    if __name__ == "__main__":
        asyncio.run(main())

### JavaScript

    import { GoogleGenAI, Modality } from '@google/genai';

    const ai = new GoogleGenAI({ apiKey: "YOUR_API_KEY"});
    const model = 'gemini-3.1-flash-live-preview';
    const config = { responseModalities: [Modality.AUDIO] };

    async function main() {

      const session = await ai.live.connect({
        model: model,
        callbacks: {
          onopen: function () {
            console.debug('Opened');
          },
          onmessage: function (message) {
            console.debug(message);
          },
          onerror: function (e) {
            console.debug('Error:', e.message);
          },
          onclose: function (e) {
            console.debug('Close:', e.reason);
          },
        },
        config: config,
      });

      console.debug("Session started");
      // Send content...

      session.close();
    }

    main();

## Sending text

Text can be sent using `send_realtime_input` (Python) or `sendRealtimeInput` (JavaScript).

### Python

    await session.send_realtime_input(text="Hello, how are you?")

### JavaScript

    session.sendRealtimeInput({
      text: 'Hello, how are you?'
    });

## Sending audio

Audio needs to be sent as raw PCM data (raw 16-bit PCM audio, 16kHz, little-endian).

### Python

    # Assuming 'chunk' is your raw PCM audio bytes
    await session.send_realtime_input(
        audio=types.Blob(
            data=chunk,
            mime_type="audio/pcm;rate=16000"
        )
    )

### JavaScript

    // Assuming 'chunk' is a Buffer of raw PCM audio
    session.sendRealtimeInput({
      audio: {
        data: chunk.toString('base64'),
        mimeType: 'audio/pcm;rate=16000'
      }
    });

For an example of how to get the audio from the client device (e.g. the browser)
see the end-to-end example on [GitHub](https://github.com/google-gemini/gemini-live-api-examples/blob/main/gemini-live-genai-python-sdk/frontend/media-handler.js#L31-L70).

## Sending video

Video frames are sent as individual images (e.g., JPEG or PNG) at a specific frame rate (max 1 frame per second).

### Python

    # Assuming 'frame' is your JPEG-encoded image bytes
    await session.send_realtime_input(
        video=types.Blob(
            data=frame,
            mime_type="image/jpeg"
        )
    )

### JavaScript

    // Assuming 'frame' is a Buffer of JPEG-encoded image data
    session.sendRealtimeInput({
      video: {
        data: frame.toString('base64'),
        mimeType: 'image/jpeg'
      }
    });

For an example of how to get the video from the client device (e.g. the browser)
see the end-to-end example on [GitHub](https://github.com/google-gemini/gemini-live-api-examples/blob/main/gemini-live-genai-python-sdk/frontend/media-handler.js#L84-L120).

## Receiving audio

The model's audio responses are received as chunks of data.

### Python

    async for response in session.receive():
        if response.server_content and response.server_content.model_turn:
            for part in response.server_content.model_turn.parts:
                if part.inline_data:
                    audio_data = part.inline_data.data
                    # Process or play the audio data

### JavaScript

    // Inside the onmessage callback
    const content = response.serverContent;
    if (content?.modelTurn?.parts) {
      for (const part of content.modelTurn.parts) {
        if (part.inlineData) {
          const audioData = part.inlineData.data;
          // Process or play audioData (base64 encoded string)
        }
      }
    }

See the example app on GitHub to learn how to [receive the audio on your server](https://github.com/google-gemini/gemini-live-api-examples/blob/main/gemini-live-genai-python-sdk/gemini_live.py#L86-L98) and [play it in the browser](https://github.com/google-gemini/gemini-live-api-examples/blob/main/gemini-live-genai-python-sdk/frontend/media-handler.js#L145-L174).

## Receiving text

Transcriptions for both user input and model output are available in the server content.

### Python

    async for response in session.receive():
        content = response.server_content
        if content:
            if content.input_transcription:
                print(f"User: {content.input_transcription.text}")
            if content.output_transcription:
                print(f"Gemini: {content.output_transcription.text}")

### JavaScript

    // Inside the onmessage callback
    const content = response.serverContent;
    if (content?.inputTranscription) {
      console.log('User:', content.inputTranscription.text);
    }
    if (content?.outputTranscription) {
      console.log('Gemini:', content.outputTranscription.text);
    }

## Handling tool calls

The API supports tool calling (function calling). When the model requests a tool call, you must execute the function and send the response back.

### Python

    async for response in session.receive():
        if response.tool_call:
            function_responses = []
            for fc in response.tool_call.function_calls:
                # 1. Execute the function locally
                result = my_tool_function(**fc.args)

                # 2. Prepare the response
                function_responses.append(types.FunctionResponse(
                    name=fc.name,
                    id=fc.id,
                    response={"result": result}
                ))

            # 3. Send the tool response back to the session
            await session.send_tool_response(function_responses=function_responses)

### JavaScript

    // Inside the onmessage callback
    if (response.toolCall) {
      const functionResponses = [];
      for (const fc of response.toolCall.functionCalls) {
        const result = myToolFunction(fc.args);
        functionResponses.push({
          name: fc.name,
          id: fc.id,
          response: { result }
        });
      }
      session.sendToolResponse({ functionResponses });
    }

## What's next

- Read the full Live API [Capabilities](https://ai.google.dev/gemini-api/docs/live-guide) guide for key capabilities and configurations; including Voice Activity Detection and native audio features.
- Read the [Tool use](https://ai.google.dev/gemini-api/docs/live-tools) guide to learn how to integrate Live API with tools and function calling.
- Read the [Session management](https://ai.google.dev/gemini-api/docs/live-session) guide for managing long running conversations.
- Read the [Ephemeral tokens](https://ai.google.dev/gemini-api/docs/ephemeral-tokens) guide for secure authentication in [client-to-server](https://ai.google.dev/gemini-api/docs/live-api/get-started-sdk#implementation-approach) applications.
- For more information about the underlying WebSockets API, see the [WebSockets API reference](https://ai.google.dev/api/live).