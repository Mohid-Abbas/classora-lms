import React, { useState, useEffect } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiClient } from "../api/client";
import "./TeacherAttendance.css";

export default function TeacherAttendancePage() {
    const [user] = useState(JSON.parse(localStorage.getItem("current_user") || "{}"));
    const [courses, setCourses] = useState([]);
    const [students, setStudents] = useState([]);
    const [selectedCourse, setSelectedCourse] = useState("");
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [attendance, setAttendance] = useState({});
    const [search, setSearch] = useState("");
    const [existingRecord, setExistingRecord] = useState(null);
    const [loading, setLoading] = useState(false);

    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState({ type: "", text: "" });

    useEffect(() => {
        apiClient.get("/api/lms/courses/")
            .then(res => {
                const data = Array.isArray(res.data) ? res.data : (res.data.results || []);
                // Filter courses where teacher is assigned
                const myCourses = data.filter(c => 
                    c.teachers?.includes(user.id) || c.teacher?.id === user.id
                );
                setCourses(myCourses);
            })
            .catch(err => console.error("Error fetching courses", err));
    }, [user.id]);

    useEffect(() => {
        if (selectedCourse) {
            fetchCourseData();
        } else {
            setStudents([]);
            setAttendance({});
            setExistingRecord(null);
        }
    }, [selectedCourse, date]);

    const fetchCourseData = async () => {
        setLoading(true);
        try {
            // Get all students first
            const studentsRes = await apiClient.get(`/api/users/?role=STUDENT&institute=${user.institute_id}`);
            const allStudents = Array.isArray(studentsRes.data) ? studentsRes.data : (studentsRes.data.results || []);
            
            let enrolledStudents = [];
            
            // Try to get course details, but fallback to all students if it fails
            try {
                const courseRes = await apiClient.get(`/api/lms/courses/${selectedCourse}/`);
                const course = courseRes.data;
                // Check different possible field names for enrolled students
                const enrolledIds = course.enrolled_students || course.students || course.student_ids || [];
                enrolledStudents = allStudents.filter(s => enrolledIds.includes(s.id));
            } catch (courseErr) {
                console.log("Course detail endpoint failed, using all students", courseErr);
                // Fallback: use all students (filter by those who have submissions or just show all)
                enrolledStudents = allStudents;
            }
            
            setStudents(enrolledStudents);
            
            // Check for existing attendance record for this date
            const init = {};
            try {
                const attendanceRes = await apiClient.get(`/api/lms/attendance/?course=${selectedCourse}&date=${date}`);
                const records = Array.isArray(attendanceRes.data) ? attendanceRes.data : (attendanceRes.data.results || []);
                
                if (records.length > 0) {
                    setExistingRecord(records[0]);
                    // Populate from existing record
                    records[0].entries?.forEach(entry => {
                        init[entry.student] = { 
                            status: entry.status || 'PRESENT', 
                            remarks: entry.remarks || '' 
                        };
                    });
                } else {
                    setExistingRecord(null);
                }
            } catch (attErr) {
                console.log("Attendance fetch failed (may not exist yet)", attErr);
                setExistingRecord(null);
            }
            
            // Set default for students not in existing record
            enrolledStudents.forEach(s => {
                if (!init[s.id]) {
                    init[s.id] = { status: 'PRESENT', remarks: '' };
                }
            });
            
            setAttendance(init);
        } catch (err) {
            console.error("Error fetching course data:", err);
            setMessage({ type: "error", text: "Failed to load student data. " + (err.response?.status === 404 ? "Course details not found." : "Please try again.") });
        } finally {
            setLoading(false);
        }
    };

    const handleStatusChange = (studentId, status) => {
        setAttendance(prev => ({
            ...prev,
            [studentId]: { ...prev[studentId], status }
        }));
    };

    const handleRemarksChange = (studentId, remarks) => {
        setAttendance(prev => ({
            ...prev,
            [studentId]: { ...prev[studentId], remarks }
        }));
    };

    const markAll = (status) => {
        const next = { ...attendance };
        students.forEach(s => next[s.id] = { ...next[s.id], status });
        setAttendance(next);
    };

    const handleSubmit = async () => {
        setSubmitting(true);
        try {
            let recordId = existingRecord?.id;
            
            // 1. Create record if doesn't exist
            if (!existingRecord) {
                const recordRes = await apiClient.post("/api/lms/attendance/", {
                    course: selectedCourse,
                    date: date
                });
                recordId = recordRes.data.id;
            }
            
            // 2. Mark entries
            const entries = Object.keys(attendance).map(sid => ({
                student_id: sid,
                status: attendance[sid].status,
                remarks: attendance[sid].remarks
            }));
            
            await apiClient.post(`/api/lms/attendance/${recordId}/mark_attendance/`, { entries });
            setMessage({ type: "success", text: existingRecord ? "Attendance updated!" : "Attendance recorded successfully!" });
            
            // Refresh to get updated record
            fetchCourseData();
        } catch (err) {
            setMessage({ type: "error", text: "Failed to record attendance." });
        } finally {
            setSubmitting(false);
        }
    };

    const getAttendanceStats = () => {
        const entries = Object.values(attendance);
        const total = entries.length;
        const present = entries.filter(a => a.status === 'PRESENT').length;
        const absent = entries.filter(a => a.status === 'ABSENT').length;
        const late = entries.filter(a => a.status === 'LATE').length;
        return { total, present, absent, late };
    };

    const filteredStudents = students.filter(s => 
        s.full_name?.toLowerCase().includes(search.toLowerCase()) ||
        s.email?.toLowerCase().includes(search.toLowerCase())
    );

    const stats = getAttendanceStats();

    return (
        <DashboardLayout user={user}>
            <div className="attendance-page">
                <div className="attendance-header">
                    <div className="attendance-title">
                        <h1>Attendance</h1>
                        <p>Mark and track student attendance for your courses</p>
                    </div>
                </div>

                {message.text && (
                    <div className={`attendance-message ${message.type}`}>
                        <span className="material-icons-round">
                            {message.type === 'success' ? 'check_circle' : 'error'}
                        </span>
                        {message.text}
                        <button onClick={() => setMessage({ type: "", text: "" })}>×</button>
                    </div>
                )}

                <div className="attendance-filters">
                    <div className="filter-group">
                        <label>Course</label>
                        <select value={selectedCourse} onChange={(e) => setSelectedCourse(e.target.value)}>
                            <option value="">Select your course</option>
                            {courses.map(c => (
                                <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
                            ))}
                        </select>
                    </div>
                    <div className="filter-group">
                        <label>Date</label>
                        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
                    </div>
                    <div className="filter-group">
                        <label>Search Student</label>
                        <input 
                            type="text" 
                            placeholder="Search by name..."
                            value={search} 
                            onChange={(e) => setSearch(e.target.value)} 
                        />
                    </div>
                </div>

                {selectedCourse && (
                    <>
                        <div className="attendance-stats">
                            <div className="stat-card">
                                <span className="stat-value">{stats.total}</span>
                                <span className="stat-label">Total Students</span>
                            </div>
                            <div className="stat-card present">
                                <span className="stat-value">{stats.present}</span>
                                <span className="stat-label">Present</span>
                            </div>
                            <div className="stat-card absent">
                                <span className="stat-value">{stats.absent}</span>
                                <span className="stat-label">Absent</span>
                            </div>
                            <div className="stat-card late">
                                <span className="stat-value">{stats.late}</span>
                                <span className="stat-label">Late</span>
                            </div>
                        </div>

                        <div className="attendance-actions-bar">
                            <div className="bulk-actions">
                                <span>Mark All:</span>
                                <button className="bulk-btn present" onClick={() => markAll('PRESENT')}>
                                    <span className="material-icons-round">check_circle</span> Present
                                </button>
                                <button className="bulk-btn absent" onClick={() => markAll('ABSENT')}>
                                    <span className="material-icons-round">cancel</span> Absent
                                </button>
                                <button className="bulk-btn late" onClick={() => markAll('LATE')}>
                                    <span className="material-icons-round">schedule</span> Late
                                </button>
                            </div>
                            {existingRecord && (
                                <span className="existing-badge">
                                    <span className="material-icons-round">history</span>
                                    Previously recorded
                                </span>
                            )}
                        </div>
                    </>
                )}

                {selectedCourse ? (
                    loading ? (
                        <div className="attendance-empty">
                            <span className="material-icons-round">sync</span>
                            <p>Loading students...</p>
                        </div>
                    ) : filteredStudents.length === 0 ? (
                        <div className="attendance-empty">
                            <span className="material-icons-round">group_off</span>
                            <p>No students found{search ? ' matching your search' : ' enrolled in this course'}</p>
                        </div>
                    ) : (
                        <div className="attendance-list">
                            {filteredStudents.map(s => (
                                <div key={s.id} className={`attendance-row ${attendance[s.id]?.status?.toLowerCase()}`}>
                                    <div className="student-info">
                                        <div className="student-avatar">
                                            <span className="material-icons-round">person</span>
                                        </div>
                                        <div className="student-details">
                                            <span className="student-name">{s.full_name}</span>
                                            <span className="student-id">{s.email}</span>
                                        </div>
                                    </div>
                                    <div className="status-toggle">
                                        <button 
                                            className={`status-btn ${attendance[s.id]?.status === 'PRESENT' ? 'active' : ''}`}
                                            onClick={() => handleStatusChange(s.id, 'PRESENT')}
                                            title="Present"
                                        >
                                            <span className="material-icons-round">check</span>
                                            Present
                                        </button>
                                        <button 
                                            className={`status-btn ${attendance[s.id]?.status === 'ABSENT' ? 'active' : ''}`}
                                            onClick={() => handleStatusChange(s.id, 'ABSENT')}
                                            title="Absent"
                                        >
                                            <span className="material-icons-round">close</span>
                                            Absent
                                        </button>
                                        <button 
                                            className={`status-btn ${attendance[s.id]?.status === 'LATE' ? 'active' : ''}`}
                                            onClick={() => handleStatusChange(s.id, 'LATE')}
                                            title="Late"
                                        >
                                            <span className="material-icons-round">schedule</span>
                                            Late
                                        </button>
                                    </div>
                                    <div className="remarks-field">
                                        <input 
                                            type="text" 
                                            placeholder="Add remarks..."
                                            value={attendance[s.id]?.remarks || ""} 
                                            onChange={(e) => handleRemarksChange(s.id, e.target.value)}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    )
                ) : (
                    <div className="attendance-empty">
                        <span className="material-icons-round">event_note</span>
                        <h3>Select a course to start marking attendance</h3>
                        <p>Choose one of your courses from the dropdown above</p>
                    </div>
                )}

                {selectedCourse && students.length > 0 && (
                    <div className="attendance-footer">
                        <button 
                            className="submit-btn" 
                            onClick={handleSubmit} 
                            disabled={submitting}
                        >
                            <span className="material-icons-round">save</span>
                            {submitting ? "Saving..." : existingRecord ? "Update Attendance" : "Record Attendance"}
                        </button>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
