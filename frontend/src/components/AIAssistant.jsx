import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import './AIAssistant.css';

export default function AIAssistant({ user }) {
    const [activeTab, setActiveTab] = useState('chat');
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [aiStatus, setAiStatus] = useState({ available: false, model: null });
    
    // Role-based feature availability
    const userRole = user?.role || 'STUDENT';
    const isAdmin = userRole === 'ADMIN';
    const isTeacher = userRole === 'TEACHER';
    const isStudent = userRole === 'STUDENT';
    
    // Quiz generation (Teachers and Students)
    const canGenerateQuiz = isTeacher || isStudent;
    const [quizForm, setQuizForm] = useState({
        topic: '',
        num_questions: 5,
        difficulty: 'medium'
    });
    const [generatedQuiz, setGeneratedQuiz] = useState(null);
    const [courses, setCourses] = useState([]);
    const [selectedCourse, setSelectedCourse] = useState('');
    const [quizTitle, setQuizTitle] = useState('');
    const [saveSuccess, setSaveSuccess] = useState(null);
    
    // Feedback (Admin: all, Teacher: students only)
    const canGiveFeedback = isAdmin || isTeacher;
    const [feedbackTarget, setFeedbackTarget] = useState('student'); // For admin: student, teacher, department
    const [feedbackUsers, setFeedbackUsers] = useState([]);
    const [selectedFeedbackUser, setSelectedFeedbackUser] = useState('');
    const [departments, setDepartments] = useState([]);
    const [selectedDepartment, setSelectedDepartment] = useState('');
    const [feedbackForm, setFeedbackForm] = useState({
        assignment_text: '',
        rubric: '',
        target_role: 'student'
    });
    const [generatedFeedback, setGeneratedFeedback] = useState(null);
    
    // Recommendations (All roles, but context varies)
    const canGiveRecommendations = true;
    const [recommendationsTarget, setRecommendationsTarget] = useState('self'); // For admin: can recommend for others
    const [recommendationsForm, setRecommendationsForm] = useState({
        student_performance: '',
        subjects: '',
        target_role: userRole.toLowerCase()
    });
    const [generatedRecommendations, setGeneratedRecommendations] = useState(null);
    
    // Student practice features
    const [practiceMode, setPracticeMode] = useState('quiz'); // quiz, flashcards, summary
    const [flashcards, setFlashcards] = useState([]);
    const [topicSummary, setTopicSummary] = useState('');

    useEffect(() => {
        checkAIStatus();
        if (canGenerateQuiz) fetchCourses();
        if (isAdmin) {
            fetchAllUsers();
            fetchDepartments();
        }
        // Role-specific welcome message
        const welcomeContent = getWelcomeMessage(userRole);
        setMessages([{
            role: 'assistant',
            content: welcomeContent
        }]);
    }, [userRole]);

    const getWelcomeMessage = (role) => {
        const baseMessage = "Hello! I'm your AI assistant for Classora LMS.\n\n";
        switch(role) {
            case 'ADMIN':
                return baseMessage + "As an admin, I can help you:\n• Give feedback to students, teachers, or departments\n• Create recommendations for different roles\n• Chat about institutional matters\n• Analyze performance data\n\nHow can I assist you today?";
            case 'TEACHER':
                return baseMessage + "As a teacher, I can help you:\n• Generate quizzes for your courses\n• Give feedback on student assignments\n• Create study recommendations for students\n• Chat about teaching strategies\n\nHow can I help you today?";
            case 'STUDENT':
                return baseMessage + "As a student, I can help you:\n• Generate practice quizzes\n• Create flashcards for studying\n• Summarize topics for quick review\n• Give study recommendations\n• Chat about your courses\n\nHow can I help you today?";
            default:
                return baseMessage + "How can I help you today?";
        }
    };

    const fetchCourses = async () => {
        try {
            const response = await apiClient.get('/api/lms/courses/');
            const coursesData = response.data.results || response.data;
            setCourses(coursesData);
        } catch (error) {
            console.error('Error fetching courses:', error);
        }
    };

    const fetchAllUsers = async () => {
        try {
            const response = await apiClient.get('/api/users/');
            const usersData = response.data.results || response.data;
            setFeedbackUsers(usersData);
        } catch (error) {
            console.error('Error fetching users:', error);
        }
    };

    const fetchDepartments = async () => {
        try {
            const response = await apiClient.get('/api/lms/departments/');
            const deptsData = response.data.results || response.data;
            setDepartments(deptsData);
        } catch (error) {
            console.error('Error fetching departments:', error);
        }
    };

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
        setSaveSuccess(null);
        try {
            const response = await apiClient.post('/api/lms/ai/generate-quiz/', quizForm);
            if (response.data.questions) {
                setGeneratedQuiz(response.data.questions);
                // Auto-generate quiz title based on topic
                setQuizTitle(`${quizForm.topic} - AI Generated Quiz`);
            } else if (response.data.error) {
                alert(response.data.error);
            }
        } catch (error) {
            if (error.response?.status === 429) {
                alert('API quota limit reached. Please wait a minute and try again.');
            } else {
                alert('Failed to generate quiz questions. Please try again.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const saveQuizToCourse = async () => {
        if (!selectedCourse) {
            alert('Please select a course');
            return;
        }
        if (!quizTitle.trim()) {
            alert('Please enter a quiz title');
            return;
        }

        setIsLoading(true);
        try {
            const response = await apiClient.post('/api/lms/ai/save-quiz/', {
                course_id: selectedCourse,
                questions: generatedQuiz,
                quiz_title: quizTitle,
                quiz_description: `AI-generated quiz about ${quizForm.topic}`,
                time_limit: 30
            });
            
            if (response.data.success) {
                setSaveSuccess({
                    message: response.data.message,
                    quizId: response.data.quiz_id,
                    courseName: response.data.course_name
                });
                alert(`Quiz saved successfully to ${response.data.course_name}!`);
            }
        } catch (error) {
            alert(error.response?.data?.error || 'Failed to save quiz to course');
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
                    
                    {/* Save Quiz to Course Section */}
                    <div className="save-quiz-section">
                        <h5>Save Quiz to Course</h5>
                        <div className="form-group">
                            <label>Select Course:</label>
                            <select
                                value={selectedCourse}
                                onChange={(e) => setSelectedCourse(e.target.value)}
                                disabled={courses.length === 0}
                            >
                                <option value="">-- Select a Course --</option>
                                {courses.map((course) => (
                                    <option key={course.id} value={course.id}>
                                        {course.name} ({course.code})
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Quiz Title:</label>
                            <input
                                type="text"
                                value={quizTitle}
                                onChange={(e) => setQuizTitle(e.target.value)}
                                placeholder="Enter quiz title"
                            />
                        </div>
                        <button 
                            onClick={saveQuizToCourse} 
                            disabled={isLoading || !selectedCourse}
                            className="save-btn"
                        >
                            {isLoading ? 'Saving...' : 'Save Quiz to Course'}
                        </button>
                        
                        {saveSuccess && (
                            <div className="save-success">
                                <span className="material-icons-round">check_circle</span>
                                <p>{saveSuccess.message}</p>
                                <p>Course: {saveSuccess.courseName}</p>
                            </div>
                        )}
                    </div>
                    
                    <hr />
                    
                    {/* Generated Questions */}
                    <h5>Preview Questions</h5>
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
                <h3>
                    {isAdmin ? 'Generate Performance Feedback' : 'Generate Assignment Feedback'}
                </h3>
                
                {/* Admin Target Selection */}
                {isAdmin && (
                    <div className="form-group">
                        <label>Feedback For:</label>
                        <select
                            value={feedbackTarget}
                            onChange={(e) => {
                                setFeedbackTarget(e.target.value);
                                setFeedbackForm({...feedbackForm, target_role: e.target.value});
                            }}
                        >
                            <option value="student">Student</option>
                            <option value="teacher">Teacher</option>
                            <option value="department">Department</option>
                        </select>
                    </div>
                )}
                
                {/* User/Department Selection for Admin */}
                {isAdmin && feedbackTarget === 'department' && (
                    <div className="form-group">
                        <label>Select Department:</label>
                        <select
                            value={selectedDepartment}
                            onChange={(e) => setSelectedDepartment(e.target.value)}
                        >
                            <option value="">-- Select Department --</option>
                            {departments.map(dept => (
                                <option key={dept.id} value={dept.id}>{dept.name}</option>
                            ))}
                        </select>
                    </div>
                )}
                
                {isAdmin && (feedbackTarget === 'student' || feedbackTarget === 'teacher') && (
                    <div className="form-group">
                        <label>Select {feedbackTarget === 'student' ? 'Student' : 'Teacher'}:</label>
                        <select
                            value={selectedFeedbackUser}
                            onChange={(e) => setSelectedFeedbackUser(e.target.value)}
                        >
                            <option value="">-- Select User --</option>
                            {feedbackUsers
                                .filter(u => u.role.toUpperCase() === feedbackTarget.toUpperCase())
                                .map(user => (
                                    <option key={user.id} value={user.id}>
                                        {user.full_name} ({user.email})
                                    </option>
                                ))}
                        </select>
                    </div>
                )}
                
                <div className="form-group">
                    <label>
                        {isAdmin 
                            ? (feedbackTarget === 'department' ? 'Department Performance Data:' : 'Performance/Work Sample:')
                            : 'Assignment Text:'
                        }
                    </label>
                    <textarea
                        value={feedbackForm.assignment_text}
                        onChange={(e) => setFeedbackForm({...feedbackForm, assignment_text: e.target.value})}
                        placeholder={
                            isAdmin 
                                ? (feedbackTarget === 'department' 
                                    ? "Describe department performance, metrics, and observations..."
                                    : "Paste work sample, performance data, or materials to review...")
                                : "Paste the student's assignment submission here..."
                        }
                        rows={6}
                    />
                </div>
                <div className="form-group">
                    <label>
                        {isAdmin ? 'Evaluation Criteria (Optional):' : 'Rubric (Optional):'}
                    </label>
                    <textarea
                        value={feedbackForm.rubric}
                        onChange={(e) => setFeedbackForm({...feedbackForm, rubric: e.target.value})}
                        placeholder={
                            isAdmin 
                                ? "Enter evaluation criteria or standards..."
                                : "Enter grading criteria or rubric..."
                        }
                        rows={3}
                    />
                </div>
                <button onClick={generateFeedback} disabled={isLoading} className="generate-btn">
                    {isLoading ? 'Generating...' : (isAdmin ? 'Generate Performance Feedback' : 'Generate Feedback')}
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
                <h3>
                    {isAdmin ? 'Generate Recommendations' : 'Generate Study Recommendations'}
                </h3>
                
                {/* Admin Target Selection */}
                {isAdmin && (
                    <div className="form-group">
                        <label>Recommendations For:</label>
                        <select
                            value={recommendationsTarget}
                            onChange={(e) => {
                                setRecommendationsTarget(e.target.value);
                                setRecommendationsForm({...recommendationsForm, target_role: e.target.value});
                            }}
                        >
                            <option value="student">Students</option>
                            <option value="teacher">Teachers</option>
                            <option value="department">Department</option>
                            <option value="institute">Institute</option>
                        </select>
                    </div>
                )}
                
                <div className="form-group">
                    <label>
                        {isAdmin 
                            ? (recommendationsTarget === 'department' || recommendationsTarget === 'institute'
                                ? 'Performance Metrics & Data:'
                                : 'Performance Description:')
                            : 'Student Performance:'
                        }
                    </label>
                    <textarea
                        value={recommendationsForm.student_performance}
                        onChange={(e) => setRecommendationsForm({...recommendationsForm, student_performance: e.target.value})}
                        placeholder={
                            isAdmin 
                                ? (recommendationsTarget === 'department' || recommendationsTarget === 'institute'
                                    ? "Describe performance metrics, goals, challenges, and current status..."
                                    : "Describe the person's performance, achievements, and areas for growth...")
                                : "Describe the student's current performance, grades, strengths, and weaknesses..."
                        }
                        rows={4}
                    />
                </div>
                <div className="form-group">
                    <label>
                        {isAdmin 
                            ? (recommendationsTarget === 'department' || recommendationsTarget === 'institute'
                                ? 'Context/Environment:'
                                : 'Subjects/Courses:')
                            : 'Subjects/Courses:'
                        }
                    </label>
                    <textarea
                        value={recommendationsForm.subjects}
                        onChange={(e) => setRecommendationsForm({...recommendationsForm, subjects: e.target.value})}
                        placeholder={
                            isAdmin 
                                ? (recommendationsTarget === 'department' || recommendationsTarget === 'institute'
                                    ? "Describe context, resources, constraints, and environment..."
                                    : "List the subjects or courses...")
                                : "List the subjects or courses the student is taking..."
                        }
                        rows={3}
                    />
                </div>
                <button onClick={generateRecommendations} disabled={isLoading} className="generate-btn">
                    {isLoading ? 'Generating...' : 'Generate Recommendations'}
                </button>
            </div>
            
            {generatedRecommendations && (
                <div className="generated-content">
                    <h4>
                        {isAdmin 
                            ? `${recommendationsTarget.charAt(0).toUpperCase() + recommendationsTarget.slice(1)} Recommendations`
                            : 'Study Recommendations'
                        }
                    </h4>
                    
                    {generatedRecommendations.focus_areas && (
                        <div className="recommendation-section">
                            <p><strong>Focus Areas:</strong></p>
                            <ul>
                                {generatedRecommendations.focus_areas?.map((area, i) => (
                                    <li key={i}>{area}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    
                    {generatedRecommendations.study_schedule && (
                        <div className="recommendation-section">
                            <p><strong>Schedule/Plan:</strong></p>
                            <p>{generatedRecommendations.study_schedule}</p>
                        </div>
                    )}
                    
                    {generatedRecommendations.improvement_plan && (
                        <div className="recommendation-section">
                            <p><strong>Improvement Plan:</strong></p>
                            <p>{generatedRecommendations.improvement_plan}</p>
                        </div>
                    )}
                    
                    {generatedRecommendations.resources && (
                        <div className="recommendation-section">
                            <p><strong>Recommended Resources:</strong></p>
                            <ul>
                                {generatedRecommendations.resources?.map((resource, i) => (
                                    <li key={i}>{resource}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    
                    {generatedRecommendations.tips && (
                        <div className="recommendation-section">
                            <p><strong>{isAdmin ? 'Action Items' : 'Study Tips'}:</strong></p>
                            <ul>
                                {generatedRecommendations.tips?.map((tip, i) => (
                                    <li key={i}>{tip}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );

    // Student practice features
    const generateFlashcards = async () => {
        if (!quizForm.topic.trim()) {
            alert('Please enter a topic');
            return;
        }
        setIsLoading(true);
        try {
            const prompt = `Create 10 flashcards for studying ${quizForm.topic}. Format as JSON array with each card having: term (the concept/question), definition (the answer/explanation). Make them suitable for student studying.`;
            const response = await apiClient.post('/api/lms/ai/chat/', { message: prompt });
            
            // Parse flashcards from response
            const text = response.data.response;
            const jsonMatch = text.match(/\[[\s\S]*\]/);
            if (jsonMatch) {
                const cards = JSON.parse(jsonMatch[0]);
                setFlashcards(cards);
                setPracticeMode('flashcards');
            }
        } catch (error) {
            alert('Failed to generate flashcards');
        } finally {
            setIsLoading(false);
        }
    };

    const generateSummary = async () => {
        if (!quizForm.topic.trim()) {
            alert('Please enter a topic');
            return;
        }
        setIsLoading(true);
        try {
            const prompt = `Create a concise study summary for ${quizForm.topic}. Include key concepts, important points, and study tips. Keep it under 500 words and student-friendly.`;
            const response = await apiClient.post('/api/lms/ai/chat/', { message: prompt });
            setTopicSummary(response.data.response);
            setPracticeMode('summary');
        } catch (error) {
            alert('Failed to generate summary');
        } finally {
            setIsLoading(false);
        }
    };

    const renderStudentPractice = () => (
        <div className="ai-tool-container">
            <div className="tool-form">
                <h3>Study Practice Tools</h3>
                <div className="form-group">
                    <label>Topic:</label>
                    <input
                        type="text"
                        value={quizForm.topic}
                        onChange={(e) => setQuizForm({...quizForm, topic: e.target.value})}
                        placeholder="e.g., Photosynthesis, World War II, Calculus"
                    />
                </div>
                <div className="practice-modes">
                    <button 
                        onClick={() => setPracticeMode('quiz')} 
                        className={`mode-btn ${practiceMode === 'quiz' ? 'active' : ''}`}
                    >
                        <span className="material-icons-round">quiz</span>
                        Practice Quiz
                    </button>
                    <button 
                        onClick={generateFlashcards} 
                        disabled={isLoading}
                        className={`mode-btn ${practiceMode === 'flashcards' ? 'active' : ''}`}
                    >
                        <span className="material-icons-round">style</span>
                        Flashcards
                    </button>
                    <button 
                        onClick={generateSummary} 
                        disabled={isLoading}
                        className={`mode-btn ${practiceMode === 'summary' ? 'active' : ''}`}
                    >
                        <span className="material-icons-round">summarize</span>
                        Summary
                    </button>
                </div>
                
                {practiceMode === 'quiz' && (
                    <>
                        <div className="form-row">
                            <div className="form-group">
                                <label>Questions:</label>
                                <select
                                    value={quizForm.num_questions}
                                    onChange={(e) => setQuizForm({...quizForm, num_questions: parseInt(e.target.value)})}
                                >
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
                            {isLoading ? 'Generating...' : 'Generate Practice Quiz'}
                        </button>
                    </>
                )}
            </div>
            
            {practiceMode === 'flashcards' && flashcards.length > 0 && (
                <div className="generated-content">
                    <h4>Flashcards for {quizForm.topic}</h4>
                    <div className="flashcards-container">
                        {flashcards.map((card, idx) => (
                            <div key={idx} className="flashcard">
                                <div className="flashcard-front">{card.term}</div>
                                <div className="flashcard-back">{card.definition}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
            
            {practiceMode === 'summary' && topicSummary && (
                <div className="generated-content">
                    <h4>Study Summary: {quizForm.topic}</h4>
                    <div className="summary-text">{topicSummary}</div>
                </div>
            )}
            
            {practiceMode === 'quiz' && generatedQuiz && (
                <div className="generated-content">
                    <h4>Practice Quiz: {quizForm.topic}</h4>
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

    // Render role-based tabs
    const renderTabs = () => {
        const tabs = [
            { id: 'chat', label: 'Chat', icon: 'chat', show: true }
        ];

        if (isAdmin) {
            tabs.push(
                { id: 'feedback', label: 'Feedback', icon: 'rate_review', show: true },
                { id: 'recommendations', label: 'Recommendations', icon: 'lightbulb', show: true }
            );
        } else if (isTeacher) {
            tabs.push(
                { id: 'quiz', label: 'Quiz Generator', icon: 'quiz', show: true },
                { id: 'feedback', label: 'Feedback', icon: 'rate_review', show: true },
                { id: 'recommendations', label: 'Recommendations', icon: 'lightbulb', show: true }
            );
        } else if (isStudent) {
            tabs.push(
                { id: 'practice', label: 'Study Tools', icon: 'school', show: true },
                { id: 'recommendations', label: 'Recommendations', icon: 'lightbulb', show: true }
            );
        }

        return tabs.map(tab => (
            <button
                key={tab.id}
                className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
            >
                <span className="material-icons-round">{tab.icon}</span>
                {tab.label}
            </button>
        ));
    };

    return (
        <div className="ai-assistant">
            <div className="ai-header">
                <h2>AI Assistant</h2>
                <div className="role-badge">{userRole}</div>
                <div className={`ai-status ${aiStatus.available ? 'online' : 'offline'}`}>
                    <span className="status-dot"></span>
                    {aiStatus.available ? `Online (${aiStatus.model})` : 'Offline'}
                </div>
            </div>
            
            <div className="ai-tabs">
                {renderTabs()}
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
                {activeTab === 'practice' && renderStudentPractice()}
                {activeTab === 'feedback' && renderFeedbackGenerator()}
                {activeTab === 'recommendations' && renderRecommendations()}
            </div>
        </div>
    );
}
