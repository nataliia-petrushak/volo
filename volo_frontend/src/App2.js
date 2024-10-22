import React from 'react'
import { useAudioStream } from './audioStream'

const App = () => {
  const sendBlob = (data) => {
    console.log(data)
  }
  const { startStream, stopStream } = useAudioStream(sendBlob)
  return (
    <div>
      <button
        onClick={() => {
          startStream()
        }}
      >
        start stream
      </button>
      <button
        onClick={() => {
          stopStream()
        }}
      >
        stop stream
      </button>
    </div>
  )
}

export default App