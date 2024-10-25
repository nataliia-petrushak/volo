import React, { useState, useRef } from 'react';
import './AudioInterface.css';

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
                mediaRecorder.start(250);

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
        socket.send("End")
    };

    const handleDataAvailable = (event) => {
        if (event.data.size > 0) {
            socket.send(event.data);
            setRecordedChunks(event.data);
        }
    };

    const playRecordedAudio = () => {
        if (recordedChunks.length > 0) {
            const blob = new Blob(recordedChunks, { type: 'audio/mpeg' });
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
        <div className="audio-recorder">
            <h2>Audio Recorder</h2>
            <div className="button-group">
                <button className="record-btn" onClick={startRecording} disabled={recording}>
                    🎙️ Start Recording
                </button>
                <button className="stop-btn" onClick={stopRecording} disabled={!recording}>
                    ⏹️ Stop Recording
                </button>
                <button className="play-btn" onClick={playRecordedAudio} disabled={!recordedChunks.length}>
                    ▶️ Play Audio
                </button>
                <button className="upload-btn" onClick={uploadAudio} disabled={!recordedChunks.length}>
                    ⬆️ Upload
                </button>
            </div>
            <div className="audio-player-container">
                <audio controls src={audioURL} className="audio-player"></audio>
            </div>
        </div>
    );
}
