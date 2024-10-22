import {useRef, useEffect, useState} from 'react'; // Import the socket.io client

export const useAudioStream = (timeSlice = 500) => {
  const mediaStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const [socket, setWs] = useState(null);

  async function handleConnectWebSocket(){
      const newSocket = new WebSocket(`ws://localhost:8000/voice-to-voice/ws`);

      newSocket.onopen = () => {
        console.log("Connected to socket");
      };
      newSocket.onclose = () => {
        console.log("Disconnected");
      };
      setWs(newSocket);
    }

  useEffect(() => {
     handleConnectWebSocket()

    return () => {
      if (socket) {
        socket.close(); // Close WebSocket on component unmount
      }
    };
  }, []);

  const captureUserAudio = () => {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        mediaStreamRef.current = stream;

        mediaRecorder.start(timeSlice);
        mediaRecorder.addEventListener('dataavailable', async (blobEvent) => {
          if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(blobEvent.data);
          } else {
            console.warn("Socket is not open. Cannot send data.");
          }
          // Send the audio blob to the backend via WebSocket
        });
      })
      .catch((error) => {
        console.error('Error accessing audio devices:', error);
      });
  };

  const startStream = async () => {

    captureUserAudio();
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.start();
    }
  };

  const stopStream = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => {
        if (track.readyState === 'live' && track.kind === 'audio') {
          track.stop();
        }
      });
    }
    if (socket) {
      socket.close();
      // setWs(socket);
    }
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
  }


  return {
    startStream,
    stopStream,
  };
};
