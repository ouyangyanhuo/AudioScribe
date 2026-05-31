import type { EmotionVector } from '../shared/types';
import { useI18n } from '../shared/i18n';
import type { TranslationKey } from '../shared/i18n';

const labelKeys: TranslationKey[] = [
  'emotionHappy',
  'emotionAngry',
  'emotionSad',
  'emotionAfraid',
  'emotionDisgust',
  'emotionMelancholy',
  'emotionSurprise',
  'emotionCalm',
];

export function EmotionVectorEditor({
  value,
  onChange,
}: {
  value: EmotionVector;
  onChange: (value: EmotionVector) => void;
}) {
  const { t } = useI18n();

  return (
    <div className="emotion-grid">
      {labelKeys.map((key, index) => (
        <label key={key} className="range-row">
          <span>{t(key)}</span>
          <input
            type="range"
            min="0"
            max="1.2"
            step="0.05"
            value={value[index]}
            onChange={(event) => {
              const next = [...value] as EmotionVector;
              next[index] = Number(event.target.value);
              onChange(next);
            }}
          />
          <strong>{value[index].toFixed(2)}</strong>
        </label>
      ))}
    </div>
  );
}
