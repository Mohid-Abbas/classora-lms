import React, { useState, useEffect } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import { apiClient } from "../../api/client";
import "./EnrollStudentPage.css";

export default function EnrollStudentPage() {
    const [user] = useState(JSON.parse(localStorage.getItem("current_user") || "{}"));
    const [courses, setCourses] = useState([]);
    const [students, setStudents] = useState([]);
    const [selectedCourse, setSelectedCourse] = useState("");
    const [search, setSearch] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState({ type: "", text: "" });
    const [viewMode, setViewMode] = useState("enrolled"); // 'enrolled' or 'available'

    useEffect(() => {
        fetchData();
    }, [user.institute_id]);

    const fetchData = async () => {
        try {
            const [coursesRes, studentsRes] = await Promise.all([
                apiClient.get("/api/lms/courses/"),
                apiClient.get(`/api/users/?role=STUDENT&institute=${user.institute_id}`)
            ]);
            setCourses(Array.isArray(coursesRes.data) ? coursesRes.data : (coursesRes.data.results || []));
            setStudents(Array.isArray(studentsRes.data) ? studentsRes.data : (studentsRes.data.results || []));
        } catch (err) {
            console.error(err);
        }
    };

    const toggleEnrollment = async (studentId, isEnrolled) => {
        if (!selectedCourse) return;

        setSubmitting(true);
        try {
            const course = courses.find(c => c.id === parseInt(selectedCourse));
            let updatedStudents = [...(course.students || [])];

            if (isEnrolled) {
                updatedStudents = updatedStudents.filter(id => id !== studentId);
            } else {
                updatedStudents.push(studentId);
            }

            await apiClient.patch(`/api/lms/courses/${selectedCourse}/`, { students: updatedStudents });

            setCourses(courses.map(c => c.id === parseInt(selectedCourse) ? { ...c, students: updatedStudents } : c));
            setMessage({ type: "success", text: isEnrolled ? "Student removed from course" : "Student enrolled successfully" });
            setTimeout(() => setMessage({ type: "", text: "" }), 3000);
        } catch (err) {
            setMessage({ type: "error", text: "Failed to update enrollment" });
        } finally {
            setSubmitting(false);
        }
    };

    const selectedCourseObj = courses.find(c => c.id === parseInt(selectedCourse));
    const enrolledStudents = selectedCourseObj ? students.filter(s => selectedCourseObj.students?.includes(s.id)) : [];
    const availableStudents = selectedCourseObj ? students.filter(s => !selectedCourseObj.students?.includes(s.id)) : [];
    
    const filteredAvailable = availableStudents.filter(s =>
        s.full_name.toLowerCase().includes(search.toLowerCase()) ||
        s.email.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <DashboardLayout user={user}>
            <div className="enroll-page-container">
                <div className="enroll-header">
                    <h1>Student Enrollment</h1>
                    <p>Manage course enrollments and student assignments</p>
                </div>

                {message.text && (
                    <div className={`enroll-message ${message.type}`}>
                        <span className="material-icons-round">
                            {message.type === 'success' ? 'check_circle' : 'error'}
                        </span>
                        {message.text}
                        <button onClick={() => setMessage({ type: "", text: "" })}>×</button>
                    </div>
                )}

                {/* Course Selection Grid */}
                <div className="course-selection">
                    <h3>Select a Course</h3>
                    <div className="course-cards-grid">
                        {courses.map(course => (
                            <div 
                                key={course.id}
                                className={`course-select-card ${selectedCourse === String(course.id) ? 'active' : ''}`}
                                onClick={() => { setSelectedCourse(String(course.id)); setViewMode('enrolled'); }}
                            >
                                <div className="course-select-header">
                                    <div className="course-select-icon">
                                        <span className="material-icons-round">school</span>
                                    </div>
                                    <div className="course-select-info">
                                        <h4>{course.name}</h4>
                                        <p>{course.code} • {course.semester} {course.academic_year}</p>
                                    </div>
                                </div>
                                <div className="course-select-stats">
                                    <div className="stat">
                                        <span className="material-icons-round">group</span>
                                        <span>{course.students?.length || 0} Students</span>
                                    </div>
                                    <div className="stat">
                                        <span className="material-icons-round">person</span>
                                        <span>{course.teachers?.length || 0} Teachers</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                        {courses.length === 0 && (
                            <div className="no-courses">No courses available. Create a course first.</div>
                        )}
                    </div>
                </div>

                {/* Student Management Panel */}
                {selectedCourse && (
                    <div className="student-management">
                        <div className="management-header">
                            <h3>{selectedCourseObj?.name} - Enrollment</h3>
                            <div className="view-toggle">
                                <button 
                                    className={viewMode === 'enrolled' ? 'active' : ''}
                                    onClick={() => setViewMode('enrolled')}
                                >
                                    <span className="material-icons-round">group</span>
                                    Enrolled ({enrolledStudents.length})
                                </button>
                                <button 
                                    className={viewMode === 'available' ? 'active' : ''}
                                    onClick={() => setViewMode('available')}
                                >
                                    <span className="material-icons-round">person_add</span>
                                    Add Students ({availableStudents.length})
                                </button>
                            </div>
                        </div>

                        {viewMode === 'available' && (
                            <div className="search-bar">
                                <span className="material-icons-round">search</span>
                                <input 
                                    type="text" 
                                    placeholder="Search students by name or email..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                />
                            </div>
                        )}

                        <div className="students-grid">
                            {viewMode === 'enrolled' ? (
                                enrolledStudents.length > 0 ? (
                                    enrolledStudents.map(student => (
                                        <div key={student.id} className="student-card enrolled">
                                            <div className="student-avatar">
                                                <span className="material-icons-round">person</span>
                                            </div>
                                            <div className="student-info">
                                                <h4>{student.full_name}</h4>
                                                <p>{student.email}</p>
                                            </div>
                                            <button 
                                                className="action-btn remove"
                                                onClick={() => toggleEnrollment(student.id, true)}
                                                disabled={submitting}
                                                title="Remove from course"
                                            >
                                                <span className="material-icons-round">person_remove</span>
                                            </button>
                                        </div>
                                    ))
                                ) : (
                                    <div className="empty-state">
                                        <span className="material-icons-round">group_off</span>
                                        <p>No students enrolled yet</p>
                                        <button onClick={() => setViewMode('available')}>Add Students</button>
                                    </div>
                                )
                            ) : (
                                filteredAvailable.length > 0 ? (
                                    filteredAvailable.map(student => (
                                        <div key={student.id} className="student-card available">
                                            <div className="student-avatar">
                                                <span className="material-icons-round">person</span>
                                            </div>
                                            <div className="student-info">
                                                <h4>{student.full_name}</h4>
                                                <p>{student.email}</p>
                                            </div>
                                            <button 
                                                className="action-btn add"
                                                onClick={() => toggleEnrollment(student.id, false)}
                                                disabled={submitting}
                                                title="Enroll in course"
                                            >
                                                <span className="material-icons-round">person_add</span>
                                            </button>
                                        </div>
                                    ))
                                ) : (
                                    <div className="empty-state">
                                        <span className="material-icons-round">search_off</span>
                                        <p>No available students found</p>
                                    </div>
                                )
                            )}
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
