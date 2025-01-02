import React, { useState } from 'react';

const PracticeTest = ({ test }) => {
  const [userAnswers, setUserAnswers] = useState({});
  const [showAnswers, setShowAnswers] = useState({});

  const handleAnswerChange = (index, value) => {
    setUserAnswers({
      ...userAnswers,
      [index]: value,
    });
  };

  const toggleShowAnswer = (index) => {
    setShowAnswers({
      ...showAnswers,
      [index]: !showAnswers[index],
    });
  };

  const checkAnswer = (index, correctAnswer) => {
    const userAnswer = userAnswers[index]?.trim();
    return userAnswer === correctAnswer.trim();
  };

  return (
    <div className="max-w-3xl mx-auto p-6 font-sans text-gray-800">
      <h2 className="text-2xl font-bold text-blue-600 text-center mb-6">
        Practice Test
      </h2>
      <ol className="list-decimal ml-6">
        {test.map((question, index) => (
          <li key={index} className="mb-6">
            <div className="bg-white p-4 rounded-lg shadow-md">
              <p className="text-gray-800 font-medium mb-2">{question.question}</p>
              <input
                type="text"
                value={userAnswers[index] || ''}
                onChange={(e) => handleAnswerChange(index, e.target.value)}
                placeholder="Enter your answer"
                className="w-full p-2 border border-gray-300 rounded-md mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex justify-between items-center">
                <button
                  onClick={() => toggleShowAnswer(index)}
                  className="text-sm text-blue-600 hover:underline"
                >
                  {showAnswers[index] ? 'Hide Answer' : 'Show Answer'}
                </button>
                {userAnswers[index] && (
                  <span
                    className={`text-sm font-medium ${
                      checkAnswer(index, question.correctAnswer)
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {checkAnswer(index, question.correctAnswer)
                      ? 'Correct!'
                      : 'Incorrect'}
                  </span>
                )}
              </div>
              {showAnswers[index] && (
                <p className="text-sm text-gray-600 mt-2">
                  Correct Answer: {question.correctAnswer}
                </p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
};

export default PracticeTest;
