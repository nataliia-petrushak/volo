import {useState} from "react";

export function HandleMessage (event){
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [socket, setWs] = useState(null);
  const [isResponding, setIsResponding] = useState(false);
  const [currentMessage, setCurrentMessage] = useState('');

  const newMessage = event.data;
  console.log("Received chunk:", newMessage);
    // Log each received chunk
  if (newMessage === "[END]") {
    if (currentMessage.trim()) {
        // Remove any instance of "[END]" from the message
      const finalMessage = currentMessage.replace(/\[END\]/g, '').trim();
      console.log("Final bot message before setting:", finalMessage); // Log final message before setting
      setMessages((prevMessages) => [...prevMessages, `Bot: ${finalMessage}`]);
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