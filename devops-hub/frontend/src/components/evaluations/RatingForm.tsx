import { useState } from 'react';
import { Card, Button, TextArea } from '../ui';
import Rating from '../ui/Rating';
import { useEvaluations } from '../../api/hooks';

interface RatingFormProps {
  targetType: 'agent' | 'workflow';
  targetId: string;
  targetName: string;
  executionId?: string;
  onSubmit?: () => void;
}

export default function RatingForm({
  targetType,
  targetId,
  targetName,
  executionId,
  onSubmit,
}: RatingFormProps) {
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const { addEvaluation } = useEvaluations();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) return;

    addEvaluation({
      targetType,
      targetId,
      targetName,
      rating,
      feedback,
      executionId,
    });

    setSubmitted(true);
    onSubmit?.();
  };

  if (submitted) {
    return (
      <Card>
        <div className="text-center py-4">
          <div className="text-green-500 text-4xl mb-2">✓</div>
          <p className="text-gray-700 font-medium">Thank you for your feedback!</p>
          <button
            onClick={() => {
              setSubmitted(false);
              setRating(0);
              setFeedback('');
            }}
            className="text-blue-600 text-sm mt-2 hover:underline"
          >
            Submit another evaluation
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Rate this {targetType}</h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            How would you rate your experience?
          </label>
          <Rating value={rating} onChange={setRating} size="lg" />
          {rating === 0 && (
            <p className="text-sm text-gray-400 mt-1">Click a star to rate</p>
          )}
        </div>

        <TextArea
          label="Feedback (optional)"
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Share your thoughts about this experience..."
          rows={3}
        />

        <Button type="submit" disabled={rating === 0} className="w-full">
          Submit Evaluation
        </Button>
      </form>
    </Card>
  );
}
