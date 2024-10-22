import React, { useState, useEffect } from 'react';
import './Chat.css';
import {useLocation} from "react-router-dom";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [socket, setWs] = useState(null);
  const [isResponding, setIsResponding] = useState(false);
  const [currentMessage, setCurrentMessage] = useState(''); // To accumulate bot message chunks

  const [buffers, setBuffers] = useState([]);
  const [urlQueue, setUrlQueue] = useState([])
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(null);
  const [audioElem, setAudioElem] = useState(null)

  const {pathname} = useLocation();



  useEffect(() => {
    async function handleConnectWebSocket(){
      const newSocket = new WebSocket(`ws://localhost:8000${pathname}/ws`);

      newSocket.onopen = () => {
        console.log("Connected to socket");
      };
      newSocket.onclose = () => {
        console.log("Disconnected");
      };
      setWs(newSocket);
    }
     handleConnectWebSocket()

    return () => {
      if (socket) {
        socket.close(); // Close WebSocket on component unmount
      }
    };
  }, []);
  
  async function HandleTextMessage(event) {
    const newMessage = event.data;
    console.log("Received chunk:", newMessage);
    // Log each received chunk

    if (newMessage === "[END]") {
      if (currentMessage.trim()) {
        // Remove any instance of "[END]" from the message
        const finalMessage = currentMessage.replace(/\[END\]/g, '').trim();
        console.log("Final bot message before setting:", finalMessage); // Log final message before setting
        // setMessages((prevMessages) => [...prevMessages, `Bot: ${finalMessage}`]);
      }
      setCurrentMessage(''); // Clear the buffer
      setIsResponding(false); // Allow new input
    } else {

      // Accumulate chunks into currentMessage
      setCurrentMessage((prevMessage) => {
        const updatedMessage = prevMessage + newMessage;
        console.log("Accumulating currentMessage:", updatedMessage); // Log accumulation of currentMessage
        setMessages((prevMessages) => {
          // Update last bot message or create a new one
          if (prevMessages[prevMessages.length - 1]?.startsWith("Bot: ")) {
            const newMessages = [...prevMessages];
            newMessages[newMessages.length - 1] = `Bot: ${updatedMessage}`;
            return newMessages;
          }
          return [...prevMessages, `Bot: ${updatedMessage}`];
        });
        return updatedMessage;
      });
    }
  }

  useEffect(() => {
    if (socket && pathname === "/text-to-text") {
      socket.onmessage = HandleTextMessage;
    }
  }, [socket, currentMessage, pathname]);

  useEffect(() => {
    async function HandleSpeechMessage(event) {
      const message = event.data;
      console.log(message);
      if (message === "[END]") {
        setIsResponding(false);
      }
      if (message instanceof Blob) {
        const reader = new FileReader();
        reader.onload = function () {
          const arrayBuffer = reader.result;
          setBuffers((prevBuffers) => [...prevBuffers, arrayBuffer]);  // Accumulate audio data
        };
        reader.readAsArrayBuffer(message);  // Convert Blob to ArrayBuffer for audio playback
      }
    }

    if (socket && pathname === "/text-to-speech") {
      socket.onmessage = HandleSpeechMessage;

    }
  }, [socket, pathname]);

  useEffect(() => {
    if (buffers.length > 0) {
      const audioData = new Uint8Array(buffers.flat());
      const blob = new Blob([audioData], {type: "audio/mpeg"});
      const url = window.URL.createObjectURL(blob);
      setUrlQueue((prevUrlQueue) => [...prevUrlQueue, url]);
      setBuffers([]);
    }
  }, [buffers]);

  useEffect(() => {
    const playNAudio = async () => {
      const nextUrl = urlQueue[0];
      try {
        if (urlQueue.length) {
          const audio = new Audio();
          setAudioPlaying(audio);

          audio.src = nextUrl;
          audio.autoplay = true;
          audio.preload = "auto";
          setIsPlaying(true);
          audio.onended = () => {
            setIsPlaying(false);
            setUrlQueue((prevQ) => prevQ.slice(1));
          };
          setAudioElem(audio);
        }
      } catch (error) {
        console.error("Error playing Mp3 audio:", error);
      }
    };
    if (!isPlaying && urlQueue.length > 0) {
      playNAudio();
    }
  }, [urlQueue, isPlaying]);

  const sendMessage = () => {
    if (socket && input && !isResponding) {
      console.log("Sending message to bot:", input); // Log sent message
      socket.send(input); // Send the user's input
      setMessages((prevMessages) => [...prevMessages, `You: ${input}`]); // Add user's message to the chat
      setInput('');  // Clear the input box
      setIsResponding(true); // Prevent new input until bot is finished
      setCurrentMessage(''); // Reset currentMessage for a new response
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      sendMessage();
    }
  };

  return (
      <div className="chat-container">
        <div className="chat-box">
          {messages.map((msg, index) => (
              <p key={index} className={msg.startsWith("You:") ? "user-msg" : "bot-msg"}>{msg}</p>
          ))}
        </div>
        <div className="input-container">
          <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyUp={handleKeyPress}
              placeholder="Type your message here..."
              className="input-field"
              disabled={isResponding}
          />
          <button onClick={sendMessage} className="send-button" disabled={isResponding}>Send</button>
        </div>
      </div>
  );
}

export default App;
