import React, { useState, useRef, useEffect } from 'react';
import {
  Mic,
  MicOff,
  Pause,
  Play,
  RotateCcw,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Volume2,
  FileText,
  Loader2,
} from 'lucide-react';
import { apiClient } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

export interface VoiceIntakeWidgetProps {
  onTranscribeComplete?: (transcript: string) => void;
  onExtractClick?: (transcript: string) => void;
  title?: string;
  subtitle?: string;
  extractButtonLabel?: string;
  placeholder?: string;
  initialTranscript?: string;
  isExtracting?: boolean;
}

export const VoiceIntakeWidget: React.FC<VoiceIntakeWidgetProps> = ({
  onTranscribeComplete,
  onExtractClick,
  title = 'Voice Product & Brand Intake',
  subtitle = 'Speak naturally in English or Hinglish. MarketPath captures your exact words and extracts structured specifications.',
  extractButtonLabel = 'Extract Structured Data',
  placeholder = 'Your spoken words will appear here verbatim. You can review or edit before extracting...',
  initialTranscript = '',
  isExtracting = false,
}) => {
  const { session, activeOrg } = useAuth();

  const [recordingState, setRecordingState] = useState<
    'idle' | 'recording' | 'paused' | 'transcribing' | 'transcribed' | 'error'
  >('idle');
  const [seconds, setSeconds] = useState(0);
  const [transcript, setTranscript] = useState(initialTranscript);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (initialTranscript && !transcript) {
      setTranscript(initialTranscript);
    }
  }, [initialTranscript]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, []);

  const formatTime = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startRecording = async () => {
    setStatusMessage(null);
    audioChunksRef.current = [];
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Select mime type supported by browser
      let mimeType = 'audio/webm';
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
          mimeType = 'audio/ogg';
        } else {
          mimeType = '';
        }
      }

      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        });
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);

        // Upload and transcribe
        await handleUploadAndTranscribe(audioBlob);
      };

      recorder.start(250); // collect chunks every 250ms
      setRecordingState('recording');
      setSeconds(0);

      timerRef.current = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      console.warn('Microphone permission or access error:', err);
      setRecordingState('error');
      setStatusMessage(
        'Microphone access is unavailable or denied. You can paste or type your notes directly below.'
      );
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && recordingState === 'recording') {
      mediaRecorderRef.current.pause();
      setRecordingState('paused');
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && recordingState === 'paused') {
      mediaRecorderRef.current.resume();
      setRecordingState('recording');
      timerRef.current = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    }
  };

  const stopRecording = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    setRecordingState('transcribing');
    setStatusMessage('Transcribing speech verbatim with Gemini Speech-to-Text...');
  };

  const handleUploadAndTranscribe = async (audioBlob: Blob) => {
    if (!audioBlob || audioBlob.size < 50) {
      setRecordingState('error');
      setStatusMessage('No audio was captured. Please try speaking again.');
      return;
    }

    try {
      // Convert blob to base64
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      reader.onloadend = async () => {
        try {
          const base64data = reader.result as string;
          const res = await apiClient<{
            transcript: string;
            duration_seconds: number;
            detected_language: string;
            status: string;
          }>('/api/v1/voice/transcribe', {
            method: 'POST',
            token: session?.access_token,
            organizationId: activeOrg?.id,
            body: JSON.stringify({
              audio_base64: base64data,
              mime_type: audioBlob.type || 'audio/webm',
            }),
          });

          const detectedText = res?.transcript || '';
          setTranscript(detectedText);
          setRecordingState('transcribed');

          if (detectedText.trim()) {
            setStatusMessage('Verbatim transcription completed. Verify or edit your text below.');
            if (onTranscribeComplete) {
              onTranscribeComplete(detectedText);
            }
          } else {
            setStatusMessage('No clear speech was detected. You can speak again or type notes below.');
          }
        } catch (apiErr: any) {
          console.error('Transcription API error:', apiErr);
          setRecordingState('error');
          setStatusMessage(apiErr.message || 'Speech-to-text service error. Please type notes directly below.');
        }
      };
    } catch (e: any) {
      console.error('Audio encode error:', e);
      setRecordingState('error');
      setStatusMessage('Audio processing error. You can type notes directly.');
    }
  };

  const resetRecording = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setRecordingState('idle');
    setSeconds(0);
    setStatusMessage(null);
  };

  return (
    <div className="bg-warmwhite border border-border rounded-xl p-5 shadow-xs">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-forest/10 flex items-center justify-center text-forest">
              <Mic className="w-4 h-4" />
            </div>
            <h3 className="text-base font-semibold text-charcoal">{title}</h3>
          </div>
          <p className="text-xs text-charcoal-muted mt-1">{subtitle}</p>
        </div>
      </div>

      {/* Recording Stage Visual */}
      <div className="bg-purewhite border border-border/80 rounded-lg p-4 mb-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Status & Timer */}
          <div className="flex items-center gap-3">
            {recordingState === 'recording' && (
              <div className="relative flex items-center justify-center">
                <span className="animate-ping absolute inline-flex h-8 w-8 rounded-full bg-red-400 opacity-75"></span>
                <div className="w-7 h-7 rounded-full bg-red-500 flex items-center justify-center text-purewhite text-xs font-bold">
                  REC
                </div>
              </div>
            )}
            {recordingState === 'paused' && (
              <div className="w-7 h-7 rounded-full bg-amber-500 flex items-center justify-center text-purewhite text-xs font-bold">
                II
              </div>
            )}
            {recordingState === 'transcribing' && (
              <div className="w-7 h-7 rounded-full bg-forest flex items-center justify-center text-purewhite">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            )}
            {(recordingState === 'idle' || recordingState === 'transcribed' || recordingState === 'error') && (
              <div className="w-7 h-7 rounded-full bg-charcoal/10 flex items-center justify-center text-charcoal">
                <Volume2 className="w-4 h-4" />
              </div>
            )}

            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-charcoal">
                  {recordingState === 'recording' && 'Listening to Speech...'}
                  {recordingState === 'paused' && 'Recording Paused'}
                  {recordingState === 'transcribing' && 'Transcribing Speech with Gemini...'}
                  {recordingState === 'transcribed' && 'Speech Captured'}
                  {recordingState === 'idle' && 'Ready to Record'}
                  {recordingState === 'error' && 'Ready (Type or Retry)'}
                </span>
                {(recordingState === 'recording' || recordingState === 'paused') && (
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-red-50 text-red-600 font-bold border border-red-200">
                    {formatTime(seconds)}
                  </span>
                )}
              </div>
              <p className="text-xs text-charcoal-muted">
                {statusMessage ||
                  (recordingState === 'recording'
                    ? 'Speak clearly into your microphone about your products, prices, and materials.'
                    : 'Click Start Speaking or edit the transcript below.')}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {recordingState === 'idle' && (
              <button
                type="button"
                onClick={startRecording}
                className="px-4 py-2 bg-forest text-purewhite hover:bg-forest-deep text-xs font-medium rounded-lg shadow-xs flex items-center gap-2 transition"
              >
                <Mic className="w-4 h-4" />
                Start Speaking
              </button>
            )}

            {recordingState === 'recording' && (
              <>
                <button
                  type="button"
                  onClick={pauseRecording}
                  className="px-3 py-1.5 bg-softbeige text-charcoal hover:bg-sand text-xs font-medium rounded-lg border border-border flex items-center gap-1.5 transition"
                >
                  <Pause className="w-3.5 h-3.5" />
                  Pause
                </button>
                <button
                  type="button"
                  onClick={stopRecording}
                  className="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-purewhite text-xs font-medium rounded-lg shadow-xs flex items-center gap-1.5 transition"
                >
                  <MicOff className="w-3.5 h-3.5" />
                  Stop & Transcribe
                </button>
              </>
            )}

            {recordingState === 'paused' && (
              <>
                <button
                  type="button"
                  onClick={resumeRecording}
                  className="px-3 py-1.5 bg-forest text-purewhite hover:bg-forest-deep text-xs font-medium rounded-lg shadow-xs flex items-center gap-1.5 transition"
                >
                  <Play className="w-3.5 h-3.5" />
                  Resume
                </button>
                <button
                  type="button"
                  onClick={stopRecording}
                  className="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-purewhite text-xs font-medium rounded-lg shadow-xs flex items-center gap-1.5 transition"
                >
                  <MicOff className="w-3.5 h-3.5" />
                  Done
                </button>
              </>
            )}

            {(recordingState === 'transcribed' || recordingState === 'error') && (
              <button
                type="button"
                onClick={resetRecording}
                className="px-3 py-1.5 bg-purewhite text-charcoal hover:bg-softbeige text-xs font-medium rounded-lg border border-border flex items-center gap-1.5 transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Re-record
              </button>
            )}
          </div>
        </div>

        {/* Audio Player if recorded */}
        {audioUrl && (
          <div className="mt-3 pt-3 border-t border-border/60 flex items-center gap-3">
            <span className="text-[11px] font-medium text-charcoal-muted uppercase tracking-wider">Preview Audio:</span>
            <audio src={audioUrl} controls className="h-7 w-full max-w-sm" />
          </div>
        )}
      </div>

      {/* Verbatim Transcript Box */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-charcoal flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-forest" />
            Spoken Words Detected (Verify or edit before extracting)
          </label>
          <span className="text-[11px] text-charcoal-muted">
            {transcript.length} characters
          </span>
        </div>
        <textarea
          rows={4}
          value={transcript}
          onChange={(e) => {
            setTranscript(e.target.value);
            if (onTranscribeComplete) {
              onTranscribeComplete(e.target.value);
            }
          }}
          placeholder={placeholder}
          className="w-full text-xs font-normal text-charcoal bg-purewhite border border-border rounded-lg p-3 focus:outline-none focus:ring-1 focus:ring-forest leading-relaxed resize-y"
        />
      </div>

      {/* Extract Button Footer */}
      {onExtractClick && (
        <div className="mt-4 flex items-center justify-between pt-3 border-t border-border/70">
          <p className="text-[11px] text-charcoal-muted">
            {transcript.trim()
              ? 'Click below to extract structured specifications into the master catalogue.'
              : 'Speak or paste product details above to enable extraction.'}
          </p>
          <button
            type="button"
            disabled={!transcript.trim() || isExtracting}
            onClick={() => onExtractClick(transcript.trim())}
            className="px-4 py-2 bg-forest hover:bg-forest-deep disabled:opacity-40 disabled:cursor-not-allowed text-purewhite text-xs font-semibold rounded-lg shadow-xs flex items-center gap-2 transition"
          >
            {isExtracting ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Extracting Specifications...
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                {extractButtonLabel}
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};
