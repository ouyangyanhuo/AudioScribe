import { useCallback, useRef, useState } from 'react';
import { Mic, Square, Upload, User } from 'lucide-react';
import { AudioWaveformPlayer } from '../components/AudioWaveformPlayer';
import { EmotionVectorEditor } from '../components/EmotionVectorEditor';
import { PageHeader } from '../components/PageHeader';
import { Panel } from '../components/Panel';
import { useI18n } from '../shared/i18n';
import type { EmotionVector } from '../shared/types';

type AudioSource = 'preset' | 'upload' | 'record';

const ACCEPTED_FORMATS = ['audio/wav', 'audio/mpeg', 'audio/flac', 'audio/ogg', 'audio/x-wav'];

export function SingleGenerationPage() {
  const { t } = useI18n();
  const [vector, setVector] = useState<EmotionVector>([0, 0, 0, 0, 0, 0, 0, 0]);
  const [audioSource, setAudioSource] = useState<AudioSource>('preset');

  // Upload state
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioFileName, setAudioFileName] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const revokeUrl = useCallback(() => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  }, [audioUrl]);

  const setAudioFromBlob = useCallback(
    (blob: Blob, fileName: string) => {
      revokeUrl();
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      setAudioFileName(fileName);
    },
    [revokeUrl],
  );

  const handleFile = useCallback(
    (file: File) => {
      if (!ACCEPTED_FORMATS.includes(file.type) && !file.name.match(/\.(wav|mp3|flac|ogg)$/i)) {
        return;
      }
      setAudioFromBlob(file, file.name);
    },
    [setAudioFromBlob],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setIsDragging(false), []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleRemoveAudio = useCallback(() => {
    revokeUrl();
    setAudioUrl(null);
    setAudioFileName(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [revokeUrl]);

  // Recording
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const ts = new Date();
        const pad = (n: number) => String(n).padStart(2, '0');
        const name = `recording_${ts.getFullYear()}${pad(ts.getMonth() + 1)}${pad(ts.getDate())}_${pad(ts.getHours())}${pad(ts.getMinutes())}${pad(ts.getSeconds())}.webm`;
        setAudioFromBlob(blob, name);
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
    } catch {
      // Microphone permission denied or unavailable
    }
  }, [setAudioFromBlob]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  }, []);

  const switchSource = useCallback(
    (source: AudioSource) => {
      if (isRecording) stopRecording();
      if (source !== 'upload' && source !== 'record') {
        handleRemoveAudio();
      }
      setAudioSource(source);
    },
    [isRecording, stopRecording, handleRemoveAudio],
  );

  return (
    <>
      <PageHeader title={t('singleTitle')} subtitle={t('singleSubtitle')} />
      <div className="workspace two-column">
        <Panel title={t('singleTitle')}>
          {/* Audio source selector */}
          <label className="field">
            <span>{t('audioSource')}</span>
            <div className="segmented segmented-3">
              <button
                className={audioSource === 'preset' ? 'selected' : ''}
                onClick={() => switchSource('preset')}
              >
                <User size={14} />
                {t('audioSourcePreset')}
              </button>
              <button
                className={audioSource === 'upload' ? 'selected' : ''}
                onClick={() => switchSource('upload')}
              >
                <Upload size={14} />
                {t('audioSourceUpload')}
              </button>
              <button
                className={audioSource === 'record' ? 'selected' : ''}
                onClick={() => switchSource('record')}
              >
                <Mic size={14} />
                {t('audioSourceRecord')}
              </button>
            </div>
          </label>

          {/* Preset role selector */}
          {audioSource === 'preset' && (
            <label className="field">
              <span>{t('role')}</span>
              <select>
                <option>{t('emptyState')}</option>
              </select>
            </label>
          )}

          {/* Upload zone */}
          {audioSource === 'upload' && !audioUrl && (
            <div
              className={`upload-zone${isDragging ? ' drag-over' : ''}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
            >
              <Upload size={28} />
              <span className="upload-zone-hint">{t('uploadHint')}</span>
              <span className="upload-zone-formats">{t('uploadFormats')}</span>
              <input
                ref={fileInputRef}
                type="file"
                accept="audio/*"
                onChange={handleFileInput}
                hidden
              />
            </div>
          )}

          {/* Record zone */}
          {audioSource === 'record' && !audioUrl && (
            <div className="record-zone">
              <button
                className={`record-button${isRecording ? ' recording' : ''}`}
                onClick={isRecording ? stopRecording : startRecording}
              >
                {isRecording ? <Square size={20} /> : <Mic size={24} />}
              </button>
              <span className="record-label">
                {isRecording ? t('recording') : t('recordStart')}
              </span>
            </div>
          )}

          {/* Audio waveform player (shown after upload or recording) */}
          {audioUrl && (
            <div className="field">
              <AudioWaveformPlayer
                audioUrl={audioUrl}
                fileName={audioFileName}
                onRemove={handleRemoveAudio}
              />
            </div>
          )}

          <label className="field">
            <span>{t('text')}</span>
            <textarea rows={8} placeholder={t('textPlaceholder')} />
          </label>
          <button className="primary-button">{t('generate')}</button>
          <p className="notice">{t('scaffoldNotice')}</p>
        </Panel>

        <Panel title={t('emotionControl')}>
          <div className="emotion-panel-body">
            <label className="field">
              <span>{t('emotionAlpha')}</span>
              <input type="range" min="0" max="1" step="0.05" defaultValue="1" />
            </label>
            <label className="checkbox-row">
              <input type="checkbox" />
              <span>{t('randomEmotion')}</span>
            </label>
            <EmotionVectorEditor value={vector} onChange={setVector} />
          </div>
        </Panel>
      </div>
    </>
  );
}
