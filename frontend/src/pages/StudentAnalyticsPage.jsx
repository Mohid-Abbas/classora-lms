import React, { useState, useEffect } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiClient } from "../api/client";
import "./admin/Dashboard.css";

export default function StudentAnalyticsPage() {
    const [user] = useState(JSON.parse(localStorage.getItem("current_user") || "{}"));
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [expandedCourses, setExpandedCourses] = useState(new Set());
    const [analyticsData, setAnalyticsData] = useState({
        quizzes: [],
        assignments: [],
        courses: [],
        overallStats: {
            quizAverage: 0,
            assignmentAverage: 0,
            overallScore: 0
        }
    });

    useEffect(() => {
        fetchAnalyticsData();
    }, []);

    const fetchAnalyticsData = async () => {
        try {
            setLoading(true);
            setError("");

            // Use the backend analytics API
            const analyticsRes = await apiClient.get("/api/lms/student-analytics/");
            const analytics = analyticsRes.data;

            // Process the data from backend for frontend display
            const quizStats = processQuizDataFromBackend(analytics.quizzes || []);
            const assignmentStats = processAssignmentDataFromBackend(analytics.assignments || []);
            
            // Get unique course names from the analytics data
            const courseNames = new Set();
            [...(analytics.quizzes || []), ...(analytics.assignments || [])].forEach(item => {
                courseNames.add(item.course);
            });

            // Create course objects from analytics data
            const enrolledCourses = Array.from(courseNames).map(courseName => ({
                id: courseName, // Use course name as ID for mapping
                name: courseName,
                code: courseName.split(' ')[0] || courseName // Extract code from name or use full name
            }));

            setAnalyticsData({
                quizzes: quizStats,
                assignments: assignmentStats,
                courses: enrolledCourses,
                overallStats: {
                    quizAverage: Math.round(analytics.overall_performance?.quiz_average || 0),
                    assignmentAverage: Math.round(analytics.overall_performance?.assignment_average || 0),
                    overallScore: Math.round(analytics.overall_performance?.total_average || 0)
                }
            });

        } catch (err) {
            console.error("Error fetching analytics data:", err);
            setError("Failed to load analytics data. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const processQuizDataFromBackend = (quizzes) => {
        const courseStats = {};
        
        quizzes.forEach(quiz => {
            if (!courseStats[quiz.course]) {
                courseStats[quiz.course] = {
                    courseName: quiz.course,
                    courseCode: quiz.course,
                    totalQuizzes: 0,
                    attemptedQuizzes: 0,
                    gradedQuizzes: 0,
                    totalScore: 0,
                    totalMarks: 0,
                    average: 0,
                    attempts: []
                };
            }
            
            const stats = courseStats[quiz.course];
            if (quiz.score !== null && quiz.percentage !== null) {
                stats.attemptedQuizzes++;
                stats.gradedQuizzes++;
                stats.totalScore += quiz.score || 0;
                stats.totalMarks += quiz.total_marks || 0;
                stats.attempts.push({
                    quizTitle: quiz.title,
                    score: quiz.score,
                    totalMarks: quiz.total_marks,
                    percentage: quiz.percentage,
                    submittedAt: quiz.submitted_at,
                    isGraded: true
                });
            }
            stats.totalQuizzes++;
        });
        
        // Calculate averages (only from graded quizzes)
        Object.values(courseStats).forEach(stats => {
            stats.average = stats.totalMarks > 0 ? Math.round((stats.totalScore / stats.totalMarks) * 100) : 0;
        });
        
        return courseStats;
    };

    const processAssignmentDataFromBackend = (assignments) => {
        const courseStats = {};
        
        assignments.forEach(assignment => {
            if (!courseStats[assignment.course]) {
                courseStats[assignment.course] = {
                    courseName: assignment.course,
                    courseCode: assignment.course,
                    totalAssignments: 0,
                    submittedAssignments: 0,
                    gradedAssignments: 0,
                    totalScore: 0,
                    totalMarks: 0,
                    average: 0,
                    submissions: []
                };
            }
            
            const stats = courseStats[assignment.course];
            if (assignment.score !== null && assignment.percentage !== null) {
                stats.submittedAssignments++;
                stats.gradedAssignments++;
                stats.totalScore += assignment.score || 0;
                stats.totalMarks += assignment.total_marks || 0;
                stats.submissions.push({
                    assignmentTitle: assignment.title,
                    score: assignment.score,
                    totalMarks: assignment.total_marks,
                    percentage: assignment.percentage,
                    status: "GRADED",
                    submittedAt: assignment.submitted_at,
                    feedback: "", // Backend doesn't provide feedback in analytics
                    isGraded: true
                });
            }
            stats.totalAssignments++;
        });
        
        // Calculate averages (only from graded assignments)
        Object.values(courseStats).forEach(stats => {
            stats.average = stats.totalMarks > 0 ? Math.round((stats.totalScore / stats.totalMarks) * 100) : 0;
        });
        
        return courseStats;
    };

    const processQuizData = (quizzes, attempts, studentId, courses) => {
        const studentAttempts = attempts.filter(attempt => attempt.student === studentId && attempt.score !== null);
        const courseStats = {};
        
        // Get student's quiz attempts (only graded ones)
        studentAttempts.forEach(attempt => {
            const quiz = quizzes.find(q => q.id === attempt.quiz);
            if (!quiz) return;
            
            const course = courses.find(c => c.id === quiz.course);
            if (!course) return;
            
            if (!courseStats[quiz.course]) {
                courseStats[quiz.course] = {
                    courseName: course.name,
                    courseCode: course.code,
                    totalQuizzes: 0,
                    attemptedQuizzes: 0,
                    gradedQuizzes: 0,
                    totalScore: 0,
                    totalMarks: 0,
                    average: 0,
                    attempts: []
                };
            }
            
            const stats = courseStats[quiz.course];
            stats.attemptedQuizzes++;
            stats.gradedQuizzes++;
            stats.totalScore += attempt.score || 0;
            stats.totalMarks += attempt.total_marks || 0;
            stats.attempts.push({
                quizTitle: quiz.title,
                score: attempt.score,
                totalMarks: attempt.total_marks,
                percentage: attempt.total_marks ? Math.round((attempt.score / attempt.total_marks) * 100) : 0,
                submittedAt: attempt.submitted_at,
                isGraded: true
            });
        });
        
        // Count total quizzes per course
        quizzes.forEach(quiz => {
            const course = courses.find(c => c.id === quiz.course);
            if (!course || !courseStats[quiz.course]) return;
            courseStats[quiz.course].totalQuizzes++;
        });
        
        // Calculate averages (only from graded quizzes)
        Object.values(courseStats).forEach(stats => {
            stats.average = stats.totalMarks > 0 ? Math.round((stats.totalScore / stats.totalMarks) * 100) : 0;
        });
        
        return courseStats;
    };

    const processAssignmentData = (assignments, submissions, studentId, courses) => {
        const studentSubmissions = submissions.filter(sub => sub.student === studentId && sub.status === 'GRADED' && sub.score !== null);
        const courseStats = {};
        
        // Count total assignments per course
        assignments.forEach(assignment => {
            const course = courses.find(c => c.id === assignment.course);
            if (!course) return;
            
            if (!courseStats[assignment.course]) {
                courseStats[assignment.course] = {
                    courseName: course.name,
                    courseCode: course.code,
                    totalAssignments: 0,
                    submittedAssignments: 0,
                    gradedAssignments: 0,
                    totalScore: 0,
                    totalMarks: 0,
                    average: 0,
                    submissions: []
                };
            }
            
            courseStats[assignment.course].totalAssignments++;
        });
        
        // Process student submissions (only graded ones)
        studentSubmissions.forEach(submission => {
            const assignment = assignments.find(a => a.id === submission.assignment);
            if (!assignment) return;
            
            const course = courses.find(c => c.id === assignment.course);
            if (!course || !courseStats[assignment.course]) return;
            
            const stats = courseStats[assignment.course];
            stats.submittedAssignments++;
            stats.gradedAssignments++;
            stats.totalScore += submission.score || 0;
            stats.totalMarks += assignment.total_marks || 100;
            
            stats.submissions.push({
                assignmentTitle: assignment.title,
                score: submission.score,
                totalMarks: assignment.total_marks,
                percentage: assignment.total_marks ? Math.round((submission.score / assignment.total_marks) * 100) : 0,
                status: submission.status,
                submittedAt: submission.submitted_at,
                feedback: submission.feedback,
                isGraded: true
            });
        });
        
        // Calculate averages (only from graded assignments)
        Object.values(courseStats).forEach(stats => {
            stats.average = stats.totalMarks > 0 ? Math.round((stats.totalScore / stats.totalMarks) * 100) : 0;
        });
        
        return courseStats;
    };

    const calculateOverallStats = (quizzes, assignments) => {
        const quizValues = Object.values(quizzes);
        const assignmentValues = Object.values(assignments);
        
        const quizAverage = quizValues.filter(q => q.average > 0).length > 0
            ? Math.round(quizValues.filter(q => q.average > 0).reduce((sum, stat) => sum + stat.average, 0) / quizValues.filter(q => q.average > 0).length)
            : 0;
        
        const assignmentAverage = assignmentValues.filter(a => a.average > 0).length > 0
            ? Math.round(assignmentValues.filter(a => a.average > 0).reduce((sum, stat) => sum + stat.average, 0) / assignmentValues.filter(a => a.average > 0).length)
            : 0;
        
        // Weighted overall score: 50% quizzes, 50% assignments
        const overallScore = Math.round(
            (quizAverage * 0.5) + 
            (assignmentAverage * 0.5)
        );
        
        return {
            quizAverage,
            assignmentAverage,
            overallScore
        };
    };

    const toggleCourseExpansion = (courseId) => {
        setExpandedCourses(prev => {
            const newSet = new Set(prev);
            if (newSet.has(courseId)) {
                newSet.delete(courseId);
            } else {
                newSet.add(courseId);
            }
            return newSet;
        });
    };

    const getPerformanceGrade = (score) => {
        if (score >= 90) return { grade: 'A', color: '#10b981', label: 'Excellent' };
        if (score >= 80) return { grade: 'B', color: '#2196F3', label: 'Good' };
        if (score >= 70) return { grade: 'C', color: '#f59e0b', label: 'Average' };
        if (score >= 60) return { grade: 'D', color: '#ef4444', label: 'Below Average' };
        return { grade: 'F', color: '#991b1b', label: 'Poor' };
    };

    if (error) {
        return (
            <DashboardLayout user={user}>
                <div className="dashboard-container">
                    <div className="dashboard-inner">
                        <p className="pill-error-msg">{error}</p>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    // Check if there's any performance data available
    const hasQuizData = Object.keys(analyticsData.quizzes).length > 0 && 
        Object.values(analyticsData.quizzes).some(q => q.average > 0);
    const hasAssignmentData = Object.keys(analyticsData.assignments).length > 0 && 
        Object.values(analyticsData.assignments).some(a => a.average > 0);
    const hasPerformanceData = hasQuizData || hasAssignmentData;

    if (!hasPerformanceData) {
        return (
            <DashboardLayout user={user}>
                <div className="dashboard-container">
                    <div className="dashboard-inner">
                        <div className="dashboard-header" style={{ marginBottom: '40px' }}>
                            <div className="dashboard-welcome">
                                <h1 style={{ color: '#1e293b', fontWeight: 800 }}>Performance Analytics</h1>
                                <p style={{ color: '#2196F3', fontWeight: 600 }}>STUDENT INSIGHTS</p>
                            </div>
                        </div>

                        <div className="dashboard-card">
                            <div className="card-title">
                                <span className="material-icons-round">analytics</span>
                                Performance Overview
                            </div>
                            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                                <span className="material-icons-round" style={{ fontSize: '4rem', color: '#e5e7eb', marginBottom: '20px', display: 'block' }}>
                                    assessment
                                </span>
                                <p style={{ color: '#64748b', fontSize: '1.1rem', margin: 0 }}>
                                    No performance data available yet
                                </p>
                                <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '8px' }}>
                                    Student may be new or has not attempted quizzes/assignments
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    const overallGrade = getPerformanceGrade(analyticsData.overallStats.overallScore);

    return (
        <DashboardLayout user={user}>
            <div className="dashboard-container">
                <div className="dashboard-inner">
                    <div className="dashboard-header" style={{ marginBottom: '40px' }}>
                        <div className="dashboard-welcome">
                            <h1 style={{ color: '#1e293b', fontWeight: 800 }}>Performance Analytics</h1>
                            <p style={{ color: '#2196F3', fontWeight: 600 }}>STUDENT INSIGHTS</p>
                        </div>
                    </div>

                    {/* Overall Performance Card */}
                    <div className="dashboard-card" style={{ marginBottom: '30px' }}>
                        <div className="card-title">
                            <span className="material-icons-round">analytics</span>
                            Overall Performance
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '30px' }}>
                            <div style={{ textAlign: 'center' }}>
                                <div style={{ 
                                    fontSize: '3rem', 
                                    fontWeight: 800, 
                                    color: overallGrade.color,
                                    marginBottom: '10px'
                                }}>
                                    {overallGrade.grade}
                                </div>
                                <div style={{ fontSize: '2rem', fontWeight: 700, color: '#1e293b', marginBottom: '5px' }}>
                                    {analyticsData.overallStats.overallScore}%
                                </div>
                                <div style={{ fontSize: '1rem', color: '#64748b', fontWeight: 600 }}>
                                    {overallGrade.label}
                                </div>
                            </div>
                            {hasQuizData && (
                                <div>
                                    <label style={{ fontSize: '0.8rem', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>Quiz Average</label>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#7c3aed', marginTop: '5px' }}>
                                        {analyticsData.overallStats.quizAverage}%
                                    </div>
                                </div>
                            )}
                            {hasAssignmentData && (
                                <div>
                                    <label style={{ fontSize: '0.8rem', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>Assignment Average</label>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#059669', marginTop: '5px' }}>
                                        {analyticsData.overallStats.assignmentAverage}%
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Course-wise Performance with Detailed Marks */}
                    <div className="dashboard-card">
                        <div className="card-title">
                            <span className="material-icons-round">school</span>
                            Course-wise Performance Details
                        </div>
                        {analyticsData.courses.length === 0 ? (
                            <p style={{ color: '#888', fontSize: '0.9rem', padding: '20px 0' }}>
                                No course data available. You may not be enrolled in any courses yet.
                            </p>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
                                {analyticsData.courses.map(course => {
                                    const quizStats = analyticsData.quizzes[course.id];
                                    const assignmentStats = analyticsData.assignments[course.id];
                                    
                                    const courseQuizAvg = quizStats?.average || 0;
                                    const courseAssignmentAvg = assignmentStats?.average || 0;
                                    
                                    // Only show courses that have quiz or assignment data
                                    if (courseQuizAvg === 0 && courseAssignmentAvg === 0) {
                                        return null;
                                    }
                                    
                                    const courseOverall = Math.round(
                                        (courseQuizAvg * 0.5) + 
                                        (courseAssignmentAvg * 0.5)
                                    );
                                    const courseGrade = getPerformanceGrade(courseOverall);
                                    const isExpanded = expandedCourses.has(course.id);
                                    
                                    return (
                                        <div key={course.id} style={{ border: '1px solid #e5e7eb', borderRadius: '16px', padding: '20px', backgroundColor: '#fafafa' }}>
                                            {/* Course Header */}
                                            <div 
                                                style={{
                                                    display: 'flex', 
                                                    justifyContent: 'space-between', 
                                                    alignItems: 'center', 
                                                    cursor: 'pointer',
                                                    userSelect: 'none'
                                                }}
                                                onClick={() => toggleCourseExpansion(course.id)}
                                            >
                                                <div>
                                                    <h3 style={{ margin: 0, color: '#1e293b', fontSize: '1.2rem', fontWeight: 700 }}>
                                                        {course.name}
                                                    </h3>
                                                    <span style={{ color: '#2196F3', fontWeight: 600, fontSize: '0.9rem' }}>
                                                        {course.code}
                                                    </span>
                                                </div>
                                                <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: '15px' }}>
                                                    <div>
                                                        <div style={{ fontSize: '1.5rem', fontWeight: 800, color: courseGrade.color }}>
                                                            {courseOverall}%
                                                        </div>
                                                        <span style={{ 
                                                            background: courseGrade.color, 
                                                            color: 'white', 
                                                            padding: '4px 12px', 
                                                            borderRadius: '12px', 
                                                            fontSize: '0.75rem',
                                                            fontWeight: 600
                                                        }}>
                                                            {courseGrade.grade} - {courseGrade.label}
                                                        </span>
                                                    </div>
                                                    <span className="material-icons-round" style={{ fontSize: '24px', color: '#64748b', transition: 'transform 0.2s ease', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                                                        expand_more
                                                    </span>
                                                </div>
                                            </div>
                                            
                                            {isExpanded && (
                                                <>
                                                    {/* Performance Summary */}
                                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px', marginBottom: '20px', marginTop: '20px' }}>
                                                        {quizStats && quizStats.gradedQuizzes > 0 && (
                                                            <div style={{ textAlign: 'center', padding: '15px', backgroundColor: 'white', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
                                                                <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#7c3aed' }}>
                                                                    {courseQuizAvg}%
                                                                </div>
                                                                <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '5px' }}>
                                                                    Quiz Average
                                                                </div>
                                                                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                                                                    {quizStats.gradedQuizzes} graded
                                                                </div>
                                                            </div>
                                                        )}
                                                        {assignmentStats && assignmentStats.gradedAssignments > 0 && (
                                                            <div style={{ textAlign: 'center', padding: '15px', backgroundColor: 'white', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
                                                                <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#059669' }}>
                                                                    {courseAssignmentAvg}%
                                                                </div>
                                                                <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '5px' }}>
                                                                    Assignment Average
                                                                </div>
                                                                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                                                                    {assignmentStats.gradedAssignments} graded
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                    
                                                    {/* Detailed Quiz Scores */}
                                                    {quizStats && quizStats.attempts.length > 0 && (
                                                        <div style={{ marginBottom: '20px' }}>
                                                            <h4 style={{ margin: '0 0 15px 0', color: '#374151', fontSize: '1rem', fontWeight: 600 }}>
                                                                <span className="material-icons-round" style={{ fontSize: '18px', verticalAlign: 'middle', marginRight: '8px', color: '#7c3aed' }}>quiz</span>
                                                                Quiz Scores
                                                            </h4>
                                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                                                {quizStats.attempts.map((attempt, idx) => (
                                                                    <div key={idx} style={{ 
                                                                        display: 'flex', 
                                                                        justifyContent: 'space-between', 
                                                                        alignItems: 'center',
                                                                        padding: '12px 15px',
                                                                        backgroundColor: 'white',
                                                                        borderRadius: '8px',
                                                                        border: '1px solid #e5e7eb'
                                                                    }}>
                                                                        <div style={{ flex: 1 }}>
                                                                            <div style={{ fontWeight: 600, color: '#374151', fontSize: '0.9rem' }}>
                                                                                {attempt.quizTitle}
                                                                            </div>
                                                                            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '2px' }}>
                                                                                {new Date(attempt.submittedAt).toLocaleDateString()}
                                                                            </div>
                                                                        </div>
                                                                        <div style={{ textAlign: 'right' }}>
                                                                            <div style={{ 
                                                                                fontWeight: 700, 
                                                                                fontSize: '1rem',
                                                                                color: attempt.percentage >= 70 ? '#059669' : attempt.percentage >= 40 ? '#f59e0b' : '#ef4444'
                                                                            }}>
                                                                                {attempt.score}/{attempt.totalMarks}
                                                                            </div>
                                                                            <div style={{ 
                                                                                fontSize: '0.8rem', 
                                                                                color: '#64748b',
                                                                                fontWeight: 600
                                                                            }}>
                                                                                {attempt.percentage}%
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}
                                                    
                                                    {/* Detailed Assignment Scores */}
                                                    {assignmentStats && assignmentStats.submissions.length > 0 && (
                                                        <div>
                                                            <h4 style={{ margin: '0 0 15px 0', color: '#374151', fontSize: '1rem', fontWeight: 600 }}>
                                                                <span className="material-icons-round" style={{ fontSize: '18px', verticalAlign: 'middle', marginRight: '8px', color: '#059669' }}>assignment</span>
                                                                Assignment Scores
                                                            </h4>
                                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                                                {assignmentStats.submissions.map((submission, idx) => (
                                                                    <div key={idx} style={{ 
                                                                        display: 'flex', 
                                                                        justifyContent: 'space-between', 
                                                                        alignItems: 'center',
                                                                        padding: '12px 15px',
                                                                        backgroundColor: 'white',
                                                                        borderRadius: '8px',
                                                                        border: '1px solid #e5e7eb'
                                                                    }}>
                                                                        <div style={{ flex: 1 }}>
                                                                            <div style={{ fontWeight: 600, color: '#374151', fontSize: '0.9rem' }}>
                                                                                {submission.assignmentTitle}
                                                                            </div>
                                                                            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '2px' }}>
                                                                                {new Date(submission.submittedAt).toLocaleDateString()}
                                                                            </div>
                                                                            {submission.feedback && (
                                                                                <div style={{ fontSize: '0.8rem', color: '#059669', marginTop: '4px', fontStyle: 'italic' }}>
                                                                                    💬 {submission.feedback}
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                        <div style={{ textAlign: 'right' }}>
                                                                            <div style={{ 
                                                                                fontWeight: 700, 
                                                                                fontSize: '1rem',
                                                                                color: submission.percentage >= 70 ? '#059669' : submission.percentage >= 40 ? '#f59e0b' : '#ef4444'
                                                                            }}>
                                                                                {submission.score}/{submission.totalMarks}
                                                                            </div>
                                                                            <div style={{ 
                                                                                fontSize: '0.8rem', 
                                                                                color: '#64748b',
                                                                                fontWeight: 600
                                                                            }}>
                                                                                {submission.percentage}%
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}
                                                </>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
