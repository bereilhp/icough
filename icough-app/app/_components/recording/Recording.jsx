"use client";

import { useState, useRef } from "react";
import styles from "./recording.module.css";

export default function Recording() {
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState("");
  const [audioBlob, setAudioBlob] = useState(null);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = async () => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      mediaRecorderRef.current.onstart = () => {
        setRecording(true);
        audioChunksRef.current = [];
      };
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current);
        const audioUrl = URL.createObjectURL(audioBlob);
        setAudioUrl(audioUrl);
        setAudioBlob(audioBlob);
      };
      mediaRecorderRef.current.start();
    } else {
      console.error("Audio recording is not supported in this browser.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const uploadAudio = async () => {
    if (audioBlob) {
      const formData = new FormData();
      formData.append("file", audioBlob, "audio.webm");
      setErrorMessage("");

      const API_BASE_IP = process.env.NEXT_PUBLIC_IP;
      const endpoint = `http://${API_BASE_IP}:8888/process-audio/`;

      try {
        const response = await fetch(endpoint, {
          method: "POST",
          body: formData,
        });
        if (!response.ok) {
          throw new Error(
            "Failed to process the audio. Please try recording again."
          );
        }
        const data = await response.json();
        setResult(data.results[0]);
        console.log(data);
      } catch (error) {
        console.error("Upload failed:", error);
        setResult(null);
        setErrorMessage(
          "Failed to process the audio. Please try recording again."
        );
      }
    }
  };

  return (
    <div className={styles.container}>
      <p>{recording ? "Recording..." : "Press start to record"}</p>
      {recording ? (
        <button className={styles.button} onClick={stopRecording}>
          Stop Recording
        </button>
      ) : (
        <button className={styles.button} onClick={startRecording}>
          Start Recording
        </button>
      )}
      {audioUrl && (
        <>
          <div>
            <audio src={audioUrl} controls />
            <br />
            <button className={styles.button} onClick={uploadAudio}>
              Send
            </button>
          </div>
        </>
      )}
      {result && (
        <div className={styles.result}>
          <h3>Analysis Result:</h3>
          <p>
            <strong>Classification:</strong> {result.audio}
          </p>
          <p>
            <strong>Confidence Score:</strong> {result.score.toFixed(3)}
          </p>
        </div>
      )}
      {errorMessage && <div className={styles.error}>{errorMessage}</div>}
    </div>
  );
}
