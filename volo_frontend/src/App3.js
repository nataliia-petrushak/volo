import React, { useState, useRef } from 'react';

export function App3() {
    const [recording, setRecording] = useState(false);
    const [audioURL, setAudioURL] = useState('');
    const [recordedChunks, setRecordedChunks] = useState([]);
    const [socket, setWs] = useState(null);
    const mediaRecorderRef = useRef(null);
    const audioStreamRef = useRef(null);

    React.useEffect(() => {
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
         handleConnectWebSocket()

        return () => {
          if (socket) {
            socket.close(); // Close WebSocket on component unmount
          }
        };
      }, []);

    const startRecording = () => {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then((stream) => {
                audioStreamRef.current = stream;
                const mediaRecorder = new MediaRecorder(stream);
                mediaRecorderRef.current = mediaRecorder;

                mediaRecorder.addEventListener('dataavailable', handleDataAvailable);
                mediaRecorder.start();

                setRecording(true);
            })
            .catch((error) => {
                console.error('Error accessing microphone:', error);
            });
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
        }
        if (audioStreamRef.current) {
            audioStreamRef.current.getTracks().forEach((track) => track.stop());
        }
        setRecording(false);
    };

    const handleDataAvailable = (event) => {
        if (event.data.size > 0) {
            socket.send(event.data);
            setRecordedChunks(event.data);
        }
    };

    const playRecordedAudio = () => {
        if (recordedChunks.length > 0) {
            const blob = new Blob(recordedChunks, { type: 'audio/wav' });
            const audioURL = URL.createObjectURL(blob);
            setAudioURL(audioURL);
        }
    };

    const uploadAudio = () => {
        if (recordedChunks.length > 0) {
            const file = new File(recordedChunks, 'recorded_audio.wav', { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio', file);

            fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: formData,
            })
            .then((response) => {
                if (response.ok) {
                    alert("Audio uploaded successfully!");
                } else {
                    alert("Failed to upload audio.");
                }
            })
            .catch((error) => {
                console.error('Error uploading audio:', error);
            });
        }
    };

    return (
        <div>
            <button onClick={startRecording} disabled={recording}>Start Recording</button>
            <button onClick={stopRecording} disabled={!recording}>Stop Recording</button>
            <button onClick={playRecordedAudio} disabled={!recordedChunks.length}>Play Recorded Audio</button>
            <br/><br/>
            <audio controls src={audioURL}></audio>
            <br/>
            <br/><br/>
            <button onClick={uploadAudio} disabled={!recordedChunks.length}>Upload Audio</button>
        </div>
    );
}
