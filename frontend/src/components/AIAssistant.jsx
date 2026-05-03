import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import './AIAssistant.css';

export default function AIAssistant({ user }) {
    const [activeTab, setActiveTab] = useState('chat');
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [aiStatus, setAiStatus] = useState({ available: false, model: null });
    const [quizForm, setQuizForm] = useState({
        topic: '',
        num_questions: 5,
        difficulty: 'medium'
    });
    const [generatedQuiz, setGeneratedQuiz] = useState(null);
    const [feedbackForm, setFeedbackForm] = useState({
        assignment_text: '',
        rubric: ''
    });
    const [generatedFeedback, setGeneratedFeedback] = useState(null);
    const [recommendationsForm, setRecommendationsForm] = useState({
        student_performance: '',
        subjects: ''
    });
    const [generatedRecommendations, setGeneratedRecommendations] = useState(null);

    useEffect(() => {
        checkAIStatus();
        // Add welcome message
        setMessages([{
            role: 'assistant',
            content: 'Hello! I\'m your AI assistant for Classora LMS. I can help you with:\n• Generating quiz questions\n• Providing assignment feedback\n• Creating study recommendations\n• Answering questions about your courses\n\nHow can I help you today?'
        }]);
    }, []);

    const checkAIStatus = async () => {
        try {
            const response = await apiClient.get('/api/lms/ai/status/');
            setAiStatus(response.data);
        } catch (error) {
            console.error('Error checking AI status:', error);
        }
    };

    const sendMessage = async () => {
        if (!inputMessage.trim()) return;

        const userMessage = { role: 'user', content: inputMessage };
        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsLoading(true);

        try {
            const response = await apiClient.post('/api/lms/ai/chat/', {
                message: inputMessage,
                context: `User role: ${user.role}, Institute: ${user.institute_name || 'N/A'}`
            });

            if (response.data.response) {
                const assistantMessage = { role: 'assistant', content: response.data.response };
                setMessages(prev => [...prev, assistantMessage]);
            }
        } catch (error) {
            const errorMessage = {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again later.'
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const generateQuiz = async () => {
        if (!quizForm.topic.trim()) {
            alert('Please enter a topic');
            return;
        }

        setIsLoading(true);
        try {
            const response = await apiClient.post('/api/lms/ai/generate-quiz/', quizForm);
            if (response.data.questions) {
                setGeneratedQuiz(response.data.questions);
            }
        } catch (error) {
            alert('Failed to generate quiz questions. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const generateFeedback = async () => {
        if (!feedbackForm.assignment_text.trim()) {
            alert('Please enter assignment text');
            return;
        }

        setIsLoading(true);
        try {
            const response = await apiClient.post('/api/lms/ai/generate-feedback/', feedbackForm);
            if (response.data.feedback) {
                setGeneratedFeedback(response.data.feedback);
            }
        } catch (error) {
            alert('Failed to generate feedback. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const generateRecommendations = async () => {
        if (!recommendationsForm.student_performance.trim() || !recommendationsForm.subjects.trim()) {
            alert('Please fill in all fields');
            return;
        }

        setIsLoading(true);
        try {
            const response = await apiClient.post('/api/lms/ai/generate-recommendations/', recommendationsForm);
            if (response.data.recommendations) {
                setGeneratedRecommendations(response.data.recommendations);
            }
        } catch (error) {
            alert('Failed to generate recommendations. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const renderChat = () => (
        <div className="ai-chat-container">
            <div className="chat-messages">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        <div className="message-content">
                            {msg.content.split('\n').map((line, i) => (
                                <p key={i}>{line}</p>
                            ))}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="message assistant">
                        <div className="message-content loading">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
            <div className="chat-input">
                <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Ask me anything about your courses..."
                    disabled={isLoading}
                />
                <button onClick={sendMessage} disabled={isLoading || !inputMessage.trim()}>
                    <span className="material-icons-round">send</span>
                </button>
            </div>
        </div>
    );

    const renderQuizGenerator = () => (
        <div className="ai-tool-container">
            <div className="tool-form">
                <h3>Generate Quiz Questions</h3>
                <div className="form-group">
                    <label>Topic:</label>
                    <input
                        type="text"
                        value={quizForm.topic}
                        onChange={(e) => setQuizForm({...quizForm, topic: e.target.value})}
                        placeholder="e.g., Python Programming, World War II, Biology"
                    />
                </div>
                <div className="form-row">
                    <div className="form-group">
                        <label>Number of Questions:</label>
                        <select
                            value={quizForm.num_questions}
                            onChange={(e) => setQuizForm({...quizForm, num_questions: parseInt(e.target.value)})}
                        >
                            <option value={3}>3</option>
                            <option value={5}>5</option>
                            <option value={10}>10</option>
                            <option value={15}>15</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Difficulty:</label>
                        <select
                            value={quizForm.difficulty}
                            onChange={(e) => setQuizForm({...quizForm, difficulty: e.target.value})}
                        >
                            <option value="easy">Easy</option>
                            <option value="medium">Medium</option>
                            <option value="hard">Hard</option>
                        </select>
                    </div>
                </div>
                <button onClick={generateQuiz} disabled={isLoading} className="generate-btn">
                    {isLoading ? 'Generating...' : 'Generate Quiz'}
                </button>
            </div>
            
            {generatedQuiz && (
                <div className="generated-content">
                    <h4>Generated Quiz Questions</h4>
                    {generatedQuiz.map((q, idx) => (
                        <div key={idx} className="quiz-question">
                            <p><strong>Q{idx + 1}:</strong> {q.question}</p>
                            <div className="options">
                                {q.options.map((opt, i) => (
                                    <div key={i} className={`option ${i === q.correct_answer ? 'correct' : ''}`}>
                                        {opt}
                                    </div>
                                ))}
                            </div>
                            <p className="explanation"><strong>Explanation:</strong> {q.explanation}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );

    const renderFeedbackGenerator = () => (
        <div className="ai-tool-container">
            <div className="tool-form">
                <h3>Generate Assignment Feedback</h3>
                <div className="form-group">
                    <label>Assignment Text:</label>
                    <textarea
                        value={feedbackForm.assignment_text}
                        onChange={(e) => setFeedbackForm({...feedbackForm, assignment_text: e.target.value})}
                        placeholder="Paste the student's assignment submission here..."
                        rows={6}
                    />
                </div>
                <div className="form-group">
                    <label>Rubric (Optional):</label>
                    <textarea
                        value={feedbackForm.rubric}
                        onChange={(e) => setFeedbackForm({...feedbackForm, rubric: e.target.value})}
                        placeholder="Enter grading criteria or rubric..."
                        rows={3}
                    />
                </div>
                <button onClick={generateFeedback} disabled={isLoading} className="generate-btn">
                    {isLoading ? 'Generating...' : 'Generate Feedback'}
                </button>
            </div>
            
            {generatedFeedback && (
                <div className="generated-content">
                    <h4>Generated Feedback</h4>
                    <div className="feedback-section">
                        <p><strong>Overall Score:</strong> {generatedFeedback.overall_score}/100</p>
                    </div>
                    <div className="feedback-section">
                        <p><strong>Strengths:</strong></p>
                        <ul>
                            {generatedFeedback.strengths?.map((strength, i) => (
                                <li key={i}>{strength}</li>
                            ))}
                        </ul>
                    </div>
                    <div className="feedback-section">
                        <p><strong>Areas for Improvement:</strong></p>
                        <ul>
                            {generatedFeedback.improvements?.map((improvement, i) => (
                                <li key={i}>{improvement}</li>
                            ))}
                        </ul>
                    </div>
                    <div className="feedback-section">
                        <p><strong>Detailed Feedback:</strong></p>
                        <p>{generatedFeedback.detailed_feedback}</p>
                    </div>
                </div>
            )}
        </div>
    );

    const renderRecommendations = () => (
        <div className="ai-tool-container">
            <div className="tool-form">
                <h3>Generate Study Recommendations</h3>
                <div className="form-group">
                    <label>Student Performance:</label>
                    <textarea
                        value={recommendationsForm.student_performance}
                        onChange={(e) => setRecommendationsForm({...recommendationsForm, student_performance: e.target.value})}
                        placeholder="Describe the student's current performance, grades, strengths, and weaknesses..."
                        rows={4}
                    />
                </div>
                <div className="form-group">
                    <label>Subjects/Courses:</label>
                    <textarea
                        value={recommendationsForm.subjects}
                        onChange={(e) => setRecommendationsForm({...recommendationsForm, subjects: e.target.value})}
                        placeholder="List the subjects or courses the student is taking..."
                        rows={3}
                    />
                </div>
                <button onClick={generateRecommendations} disabled={isLoading} className="generate-btn">
                    {isLoading ? 'Generating...' : 'Generate Recommendations'}
                </button>
            </div>
            
            {generatedRecommendations && (
                <div className="generated-content">
                    <h4>Study Recommendations</h4>
                    <div className="recommendation-section">
                        <p><strong>Focus Areas:</strong></p>
                        <ul>
                            {generatedRecommendations.focus_areas?.map((area, i) => (
                                <li key={i}>{area}</li>
                            ))}
                        </ul>
                    </div>
                    <div className="recommendation-section">
                        <p><strong>Study Schedule:</strong></p>
                        <p>{generatedRecommendations.study_schedule}</p>
                    </div>
                    <div className="recommendation-section">
                        <p><strong>Recommended Resources:</strong></p>
                        <ul>
                            {generatedRecommendations.resources?.map((resource, i) => (
                                <li key={i}>{resource}</li>
                            ))}
                        </ul>
                    </div>
                    <div className="recommendation-section">
                        <p><strong>Study Tips:</strong></p>
                        <ul>
                            {generatedRecommendations.tips?.map((tip, i) => (
                                <li key={i}>{tip}</li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}
        </div>
    );

    return (
        <div className="ai-assistant">
            <div className="ai-header">
                <h2>AI Assistant</h2>
                <div className={`ai-status ${aiStatus.available ? 'online' : 'offline'}`}>
                    <span className="status-dot"></span>
                    {aiStatus.available ? `Online (${aiStatus.model})` : 'Offline'}
                </div>
            </div>
            
            <div className="ai-tabs">
                <button
                    className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
                    onClick={() => setActiveTab('chat')}
                >
                    <span className="material-icons-round">chat</span>
                    Chat
                </button>
                <button
                    className={`tab ${activeTab === 'quiz' ? 'active' : ''}`}
                    onClick={() => setActiveTab('quiz')}
                >
                    <span className="material-icons-round">quiz</span>
                    Quiz Generator
                </button>
                <button
                    className={`tab ${activeTab === 'feedback' ? 'active' : ''}`}
                    onClick={() => setActiveTab('feedback')}
                >
                    <span className="material-icons-round">rate_review</span>
                    Feedback
                </button>
                <button
                    className={`tab ${activeTab === 'recommendations' ? 'active' : ''}`}
                    onClick={() => setActiveTab('recommendations')}
                >
                    <span className="material-icons-round">lightbulb</span>
                    Recommendations
                </button>
            </div>
            
            <div className="ai-content">
                {!aiStatus.available && (
                    <div className="ai-unavailable">
                        <span className="material-icons-round">error</span>
                        <p>AI service is currently unavailable. Please check your API configuration.</p>
                    </div>
                )}
                
                {activeTab === 'chat' && renderChat()}
                {activeTab === 'quiz' && renderQuizGenerator()}
                {activeTab === 'feedback' && renderFeedbackGenerator()}
                {activeTab === 'recommendations' && renderRecommendations()}
            </div>
        </div>
    );
}
