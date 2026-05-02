import React, { useState, useEffect } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiClient } from "../api/client";
import "./TeacherAttendance.css";

export default function TeacherAttendancePage() {
    const [user] = useState(JSON.parse(localStorage.getItem("current_user") || "{}"));
    const [courses, setCourses] = useState([]);
    const [students, setStudents] = useState([]);
    const [selectedCourseId, setSelectedCourseId] = useState("");
    const [selectedCourse, setSelectedCourse] = useState(null);
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [attendance, setAttendance] = useState({});
    const [search, setSearch] = useState("");
    const [existingRecord, setExistingRecord] = useState(null);
    const [loading, setLoading] = useState(false);

    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState({ type: "", text: "" });
    
    // Student view states
    const [studentAttendance, setStudentAttendance] = useState([]);
    const [studentCourses, setStudentCourses] = useState([]);
    const [attendanceStats, setAttendanceStats] = useState({ present: 0, absent: 0, late: 0, total: 0, percentage: 0 });
    const isStudent = user.role === 'STUDENT';

    useEffect(() => {
        if (isStudent) {
            // Fetch student's enrolled courses
            apiClient.get("/api/lms/courses/")
                .then(res => {
                    const data = Array.isArray(res.data) ? res.data : (res.data.results || []);
                    const enrolledCourses = data.filter(c => 
                        c.students?.includes(user.id) || c.enrolled_students?.includes(user.id)
                    );
                    setStudentCourses(enrolledCourses);
                })
                .catch(err => console.error("Error fetching courses", err));
            
            // Fetch student's attendance records
            apiClient.get(`/api/lms/attendance/?student=${user.id}`)
                .then(res => {
                    const records = Array.isArray(res.data) ? res.data : (res.data.results || []);
                    setStudentAttendance(records);
                    
                    // Calculate stats
                    let present = 0, absent = 0, late = 0, total = 0;
                    records.forEach(record => {
                        const entry = record.entries?.find(e => e.student === user.id);
                        if (entry) {
                            total++;
                            if (entry.status === 'PRESENT') present++;
                            else if (entry.status === 'ABSENT') absent++;
                            else if (entry.status === 'LATE') late++;
                        }
                    });
                    setAttendanceStats({
                        present, absent, late, total,
                        percentage: total > 0 ? Math.round((present / total) * 100) : 0
                    });
                })
                .catch(err => console.error("Error fetching attendance", err));
        } else {
            // Teacher view - fetch teacher's courses
            apiClient.get("/api/lms/courses/")
                .then(res => {
                    const data = Array.isArray(res.data) ? res.data : (res.data.results || []);
                    const myCourses = data.filter(c => 
                        c.teachers?.includes(user.id) || c.teacher?.id === user.id
                    );
                    setCourses(myCourses);
                })
                .catch(err => console.error("Error fetching courses", err));
        }
    }, [user.id, user.role, isStudent]);

    useEffect(() => {
        if (selectedCourseId) {
            // Find the course object from courses list
            const course = courses.find(c => c.id === selectedCourseId);
            setSelectedCourse(course);
            fetchCourseData();
        } else {
            setStudents([]);
            setAttendance({});
            setExistingRecord(null);
            setSelectedCourse(null);
        }
    }, [selectedCourseId, date, courses]);

    const fetchCourseData = async () => {
        setLoading(true);
        setMessage({ type: "", text: "" });
        
        let loadedStudents = [];
        let hasError = false;
        let errorMsg = "";
        
        try {
            // Get all students first - try with institute filter
            let allStudents = [];
            try {
                console.log("Fetching students for institute:", user.institute_id);
                const studentsRes = await apiClient.get(`/api/users/?role=STUDENT&institute=${user.institute_id}`);
                console.log("Students response:", studentsRes.data);
                allStudents = Array.isArray(studentsRes.data) ? studentsRes.data : (studentsRes.data.results || []);
            } catch (permErr) {
                console.log("Permission error with institute filter, trying without:", permErr.message);
                // Try without institute filter
                try {
                    const studentsRes = await apiClient.get(`/api/users/?role=STUDENT`);
                    allStudents = Array.isArray(studentsRes.data) ? studentsRes.data : (studentsRes.data.results || []);
                } catch (permErr2) {
                    console.log("Still permission denied:", permErr2.message);
                    // Teacher doesn't have permission to see students at all
                    allStudents = [];
                }
            }
            console.log("All students count:", allStudents.length);
            
            let enrolledStudents = [];
            
            // Try to get enrolled students from the already-loaded course data
            let enrolledIds = [];
            if (selectedCourse) {
                enrolledIds = selectedCourse.enrolled_students || selectedCourse.students || selectedCourse.student_ids || [];
                console.log("Enrolled IDs from course data:", enrolledIds);
            }
            
            // If no students in course data, try the detail endpoint
            if (enrolledIds.length === 0) {
                try {
                    console.log("Fetching course details for:", selectedCourseId);
                    const courseRes = await apiClient.get(`/api/lms/courses/${selectedCourseId}/`);
                    console.log("Course response:", courseRes.data);
                    const course = courseRes.data;
                    enrolledIds = course.enrolled_students || course.students || course.student_ids || [];
                    console.log("Enrolled IDs from API:", enrolledIds);
                } catch (courseErr) {
                    console.log("Course detail failed:", courseErr.message);
                }
            }
            
            // Build student list
            if (enrolledIds.length > 0 && allStudents.length > 0) {
                enrolledStudents = allStudents.filter(s => enrolledIds.includes(s.id));
            } else if (enrolledIds.length > 0) {
                // We have IDs but no student details - show message
                enrolledStudents = [];
                hasError = true;
                errorMsg = "Cannot load student details. Contact admin to check user permissions.";
            } else {
                enrolledStudents = [];
            }
            
            console.log("Final enrolled students:", enrolledStudents.length);
            loadedStudents = enrolledStudents;
            setStudents(enrolledStudents);
            
            // Check for existing attendance
            const init = {};
            try {
                const attendanceRes = await apiClient.get(`/api/lms/attendance/?course=${selectedCourseId}&date=${date}`);
                const records = Array.isArray(attendanceRes.data) ? attendanceRes.data : (attendanceRes.data.results || []);
                
                if (records.length > 0) {
                    setExistingRecord(records[0]);
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
                console.log("Attendance fetch failed:", attErr.message);
                setExistingRecord(null);
            }
            
            // Set default attendance for all students
            enrolledStudents.forEach(s => {
                if (!init[s.id]) {
                    init[s.id] = { status: 'PRESENT', remarks: '' };
                }
            });
            
            setAttendance(init);
            
        } catch (err) {
            console.error("Main error:", err);
            hasError = true;
            errorMsg = err.response?.data?.detail || err.message || "Failed to load student data";
        } finally {
            setLoading(false);
            // Only show error if we couldn't load any students
            if (hasError || loadedStudents.length === 0) {
                setMessage({ 
                    type: "error", 
                    text: loadedStudents.length === 0 && !hasError 
                        ? "No students enrolled in this course" 
                        : `Failed to load student data: ${errorMsg}` 
                });
            }
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
                // Ensure date is in YYYY-MM-DD format
                const formattedDate = new Date(date).toISOString().split('T')[0];
                console.log("Creating attendance record for course:", selectedCourseId, "date:", formattedDate);
                const recordRes = await apiClient.post("/api/lms/attendance/", {
                    course: selectedCourseId,
                    date: formattedDate
                });
                recordId = recordRes.data.id;
                setExistingRecord(recordRes.data);
            }
            
            // 2. Mark attendance for all students
            const studentIds = Object.keys(attendance);
            const entries = studentIds.map(sid => ({
                student: parseInt(sid),
                status: attendance[sid].status,
                remarks: attendance[sid].remarks
            }));
            
            console.log("Submitting attendance entries:", entries);
            await apiClient.post(`/api/lms/attendance/${recordId}/mark_attendance/`, { entries });
            setMessage({ type: "success", text: existingRecord ? "Attendance updated!" : "Attendance recorded successfully!" });
            
            // Refresh to get updated record
            fetchCourseData();
        } catch (err) {
            console.error("Submit error:", err);
            console.error("Error response:", err.response?.data);
            const errorDetail = err.response?.data?.detail || 
                              err.response?.data?.date?.[0] ||
                              err.response?.data?.course?.[0] || 
                              err.message || 
                              "Failed to record attendance.";
            setMessage({ type: "error", text: errorDetail });
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

                {/* STUDENT VIEW */}
                {isStudent && (
                    <div className="student-attendance-view">
                        {/* Stats Cards */}
                        <div className="attendance-stats">
                            <div className="stat-card">
                                <span className="stat-value">{attendanceStats.total}</span>
                                <span className="stat-label">Total Sessions</span>
                            </div>
                            <div className="stat-card present">
                                <span className="stat-value">{attendanceStats.present}</span>
                                <span className="stat-label">Present</span>
                            </div>
                            <div className="stat-card absent">
                                <span className="stat-value">{attendanceStats.absent}</span>
                                <span className="stat-label">Absent</span>
                            </div>
                            <div className="stat-card late">
                                <span className="stat-value">{attendanceStats.late}</span>
                                <span className="stat-label">Late</span>
                            </div>
                        </div>

                        {/* Attendance Percentage */}
                        <div className="attendance-percentage-card">
                            <div className="percentage-circle">
                                <span className="percentage-value">{attendanceStats.percentage}%</span>
                            </div>
                            <span className="percentage-label">Attendance Rate</span>
                        </div>

                        {/* Attendance History */}
                        <div className="attendance-history">
                            <h3>My Attendance History</h3>
                            {studentAttendance.length === 0 ? (
                                <div className="attendance-empty">
                                    <span className="material-icons-round">event_note</span>
                                    <p>No attendance records found yet.</p>
                                </div>
                            ) : (
                                <div className="attendance-list">
                                    {studentAttendance.map((record, idx) => {
                                        const entry = record.entries?.find(e => e.student === user.id);
                                        if (!entry) return null;
                                        return (
                                            <div key={idx} className={`attendance-record-item ${entry.status.toLowerCase()}`}>
                                                <div className="record-date">
                                                    <span className="material-icons-round">calendar_today</span>
                                                    {record.date}
                                                </div>
                                                <div className="record-status">
                                                    <span className={`status-badge ${entry.status.toLowerCase()}`}>
                                                        {entry.status}
                                                    </span>
                                                    {entry.remarks && (
                                                        <span className="record-remarks">{entry.remarks}</span>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* TEACHER VIEW */}
                {!isStudent && (
                    <>
                        <div className="attendance-filters">
                    <div className="filter-group">
                        <label>Course</label>
                        <select value={selectedCourseId} onChange={(e) => setSelectedCourseId(e.target.value)}>
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

                {selectedCourseId && (
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

                {selectedCourseId ? (
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
                </>
                )}

                {/* Attendance Footer - Only for Teachers */}
                {!isStudent && selectedCourseId && students.length > 0 && (
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
