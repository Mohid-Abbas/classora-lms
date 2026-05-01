import React, { useState, useEffect } from "react";
import { apiClient } from "../../api/client";
import DashboardLayout from "../../components/DashboardLayout";
import "./AdminDepartmentsPage.css";

export default function AdminDepartmentsPage() {
    const user = JSON.parse(localStorage.getItem("current_user") || "{}");
    const [departments, setDepartments] = useState([]);
    const [courses, setCourses] = useState([]);
    const [users, setUsers] = useState([]);
    const [selectedDept, setSelectedDept] = useState(null);
    const [selectedCourse, setSelectedCourse] = useState(null);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState({ type: "", text: "" });
    
    // Form states
    const [newDept, setNewDept] = useState({ name: "", code: "", description: "" });
    const [showAddDept, setShowAddDept] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const currentUser = JSON.parse(localStorage.getItem("current_user") || "{}");
            const instituteId = currentUser.institute_id;
            
            const [deptRes, courseRes, usersRes] = await Promise.all([
                apiClient.get("/api/lms/departments/"),
                apiClient.get("/api/lms/courses/"),
                apiClient.get(`/api/users/?institute=${instituteId}`)
            ]);
            
            console.log("Departments response:", deptRes.data);
            console.log("Courses response:", courseRes.data);
            console.log("Users response:", usersRes.data);
            
            const depts = Array.isArray(deptRes.data) ? deptRes.data : (deptRes.data.results || []);
            const crs = Array.isArray(courseRes.data) ? courseRes.data : (courseRes.data.results || []);
            const usrs = Array.isArray(usersRes.data) ? usersRes.data : (usersRes.data.results || []);
            
            console.log("Parsed departments:", depts);
            console.log("Parsed courses:", crs);
            console.log("Parsed users:", usrs);
            
            setDepartments(depts);
            setCourses(crs);
            setUsers(usrs);
        } catch (err) {
            console.error("Error fetching data:", err);
            console.error("Error details:", err.response?.data);
            const errorMsg = err.response?.data?.detail || err.response?.data?.message || err.message || "Failed to load data";
            setMessage({ type: "error", text: errorMsg });
        } finally {
            setLoading(false);
        }
    };

    const createDepartment = async (e) => {
        e.preventDefault();
        try {
            await apiClient.post("/api/lms/departments/", newDept);
            setMessage({ type: "success", text: "Department created successfully!" });
            setNewDept({ name: "", code: "", description: "" });
            setShowAddDept(false);
            fetchData();
        } catch (err) {
            setMessage({ type: "error", text: "Failed to create department" });
        }
    };

    const deleteDepartment = async (id) => {
        if (!window.confirm("Delete this department? All associated courses will remain but without a department.")) return;
        try {
            await apiClient.delete(`/api/lms/departments/${id}/`);
            setMessage({ type: "success", text: "Department deleted" });
            setSelectedDept(null);
            fetchData();
        } catch (err) {
            setMessage({ type: "error", text: "Failed to delete department" });
        }
    };

    const deleteCourse = async (courseId) => {
        if (!window.confirm("Delete this course? All assignments, quizzes, and submissions will be permanently deleted.")) return;
        try {
            await apiClient.delete(`/api/lms/courses/${courseId}/`);
            setMessage({ type: "success", text: "Course deleted" });
            fetchData();
        } catch (err) {
            setMessage({ type: "error", text: "Failed to delete course" });
        }
    };

    const removeUserFromCourse = async (courseId, userId, role) => {
        const action = role === "TEACHER" ? "unassign teacher" : "unenroll student";
        if (!window.confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} from this course?`)) return;
        
        try {
            await apiClient.post(`/api/lms/courses/${courseId}/remove_user/`, { user_id: userId });
            setMessage({ type: "success", text: `User ${action}ed successfully` });
            fetchData();
        } catch (err) {
            setMessage({ type: "error", text: `Failed to ${action} user` });
        }
    };

    const assignTeacher = async (courseId, teacherId) => {
        try {
            await apiClient.post(`/api/lms/courses/${courseId}/assign_teacher/`, { teacher_id: teacherId });
            setMessage({ type: "success", text: "Teacher assigned successfully" });
            fetchData();
        } catch (err) {
            const msg = err.response?.data?.detail || "Failed to assign teacher";
            setMessage({ type: "error", text: msg });
        }
    };

    const getDeptCourses = (deptId) => courses.filter(c => c.department === deptId || c.department?.id === deptId);
    
    const getCourseTeachers = (course) => {
        if (!course.teachers) return [];
        return course.teachers.map(tid => users.find(u => u.id === tid || u.id === t?.id)).filter(Boolean);
    };
    
    const getCourseStudents = (course) => {
        if (!course.students) return [];
        return course.students.map(sid => users.find(u => u.id === sid)).filter(Boolean);
    };

    const teachers = users.filter(u => u.role === "TEACHER");
    const students = users.filter(u => u.role === "STUDENT");

    if (loading) return (
        <DashboardLayout user={user}>
            <div className="admin-dept-container">
                <div className="loading">Loading departments...</div>
            </div>
        </DashboardLayout>
    );

    return (
        <DashboardLayout user={user}>
            <div className="admin-dept-container">
                <div className="admin-dept-header">
                    <h1>Departments & Courses Management</h1>
                    <button className="btn-primary" onClick={() => setShowAddDept(true)}>
                        <span className="material-icons-round">add</span> Add Department
                    </button>
                </div>

                {message.text && (
                    <div className={`message ${message.type}`}>
                        {message.text}
                        <button onClick={() => setMessage({ type: "", text: "" })}>×</button>
                    </div>
                )}

                <div className="admin-dept-layout">
                    {/* Departments Sidebar */}
                    <div className="dept-sidebar">
                        <h3>Departments ({departments.length})</h3>
                        {departments.map(dept => {
                            const deptCourses = getDeptCourses(dept.id);
                            const totalStudents = deptCourses.reduce((acc, c) => acc + (c.students?.length || 0), 0);
                            const totalTeachers = deptCourses.reduce((acc, c) => acc + (c.teachers?.length || 0), 0);
                            
                            return (
                                <div 
                                    key={dept.id} 
                                    className={`dept-card ${selectedDept?.id === dept.id ? 'active' : ''}`}
                                    onClick={() => { setSelectedDept(dept); setSelectedCourse(null); }}
                                >
                                    <div className="dept-card-header">
                                        <div className="dept-icon">
                                            <span className="material-icons-round">business</span>
                                        </div>
                                        <div className="dept-info">
                                            <div className="dept-name">{dept.name}</div>
                                            <div className="dept-code">{dept.code}</div>
                                        </div>
                                    </div>
                                    <div className="dept-stats">
                                        <span title="Courses"><span className="material-icons-round">school</span> {deptCourses.length}</span>
                                        <span title="Teachers"><span className="material-icons-round">person</span> {totalTeachers}</span>
                                        <span title="Students"><span className="material-icons-round">group</span> {totalStudents}</span>
                                    </div>
                                    <button 
                                        className="btn-delete-small"
                                        onClick={(e) => { e.stopPropagation(); deleteDepartment(dept.id); }}
                                        title="Delete department"
                                    >
                                        <span className="material-icons-round">delete</span>
                                    </button>
                                </div>
                            );
                        })}
                        
                        {departments.length === 0 && (
                            <div className="empty-state">
                                <span className="material-icons-round">business</span>
                                <p>No departments yet</p>
                            </div>
                        )}
                    </div>

                    {/* Main Content Area */}
                    <div className="dept-main-content">
                        {selectedDept ? (
                            <>
                                <div className="dept-detail-header">
                                    <h2>{selectedDept.name}</h2>
                                    <p className="dept-description">{selectedDept.description || "No description"}</p>
                                </div>

                                {/* Courses in this Department */}
                                <div className="section">
                                    <h3>Courses in {selectedDept.name}</h3>
                                    <div className="courses-grid">
                                        {getDeptCourses(selectedDept.id).map(course => (
                                            <div 
                                                key={course.id} 
                                                className={`course-card ${selectedCourse?.id === course.id ? 'active' : ''}`}
                                                onClick={() => setSelectedCourse(course)}
                                            >
                                                <div className="course-header">
                                                    <div className="course-title">{course.name}</div>
                                                    <div className="course-code">{course.code}</div>
                                                </div>
                                                <div className="course-meta">
                                                    <span>{course.semester} {course.academic_year} • Sec {course.section || 'A'}</span>
                                                    <span className={`status-badge ${course.is_published ? 'published' : 'draft'}`}>
                                                        {course.is_published ? 'Published' : 'Draft'}
                                                    </span>
                                                </div>
                                                <div className="course-stats-row">
                                                    <span><span className="material-icons-round">person</span> {course.teachers?.length || 0} Teachers</span>
                                                    <span><span className="material-icons-round">group</span> {course.students?.length || 0} Students</span>
                                                </div>
                                                <button 
                                                    className="btn-delete-course"
                                                    onClick={(e) => { e.stopPropagation(); deleteCourse(course.id); }}
                                                >
                                                    <span className="material-icons-round">delete_forever</span> Delete Course
                                                </button>
                                            </div>
                                        ))}
                                        
                                        {getDeptCourses(selectedDept.id).length === 0 && (
                                            <div className="empty-state">
                                                <p>No courses in this department</p>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Selected Course Details */}
                                {selectedCourse && (
                                    <div className="course-detail-panel">
                                        <h4>{selectedCourse.name} Management</h4>
                                        
                                        {/* Teachers Section */}
                                        <div className="manage-section">
                                            <div className="manage-header">
                                                <h5>Assigned Teachers</h5>
                                                <div className="assign-dropdown">
                                                    <select 
                                                        onChange={(e) => {
                                                            if (e.target.value) {
                                                                assignTeacher(selectedCourse.id, parseInt(e.target.value));
                                                                e.target.value = "";
                                                            }
                                                        }}
                                                    >
                                                        <option value="">+ Assign Teacher</option>
                                                        {teachers
                                                            .filter(t => !selectedCourse.teachers?.includes(t.id))
                                                            .map(t => (
                                                                <option key={t.id} value={t.id}>{t.full_name} ({t.email})</option>
                                                            ))
                                                        }
                                                    </select>
                                                </div>
                                            </div>
                                            <div className="users-list">
                                                {(selectedCourse.teachers || []).map(tid => {
                                                    const t = users.find(u => u.id === tid);
                                                    if (!t) return null;
                                                    return (
                                                        <div key={tid} className="user-chip">
                                                            <span className="material-icons-round">person</span>
                                                            <span>{t.full_name}</span>
                                                            <button 
                                                                onClick={() => removeUserFromCourse(selectedCourse.id, tid, "TEACHER")}
                                                                title="Remove teacher"
                                                            >
                                                                <span className="material-icons-round">close</span>
                                                            </button>
                                                        </div>
                                                    );
                                                })}
                                                {(selectedCourse.teachers || []).length === 0 && (
                                                    <span className="no-users">No teachers assigned</span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Students Section */}
                                        <div className="manage-section">
                                            <div className="manage-header">
                                                <h5>Enrolled Students ({selectedCourse.students?.length || 0})</h5>
                                            </div>
                                            <div className="users-list scrollable">
                                                {(selectedCourse.students || []).map(sid => {
                                                    const s = users.find(u => u.id === sid);
                                                    if (!s) return null;
                                                    return (
                                                        <div key={sid} className="user-chip student">
                                                            <span className="material-icons-round">school</span>
                                                            <span>{s.full_name}</span>
                                                            <button 
                                                                onClick={() => removeUserFromCourse(selectedCourse.id, sid, "STUDENT")}
                                                                title="Unenroll student"
                                                            >
                                                                <span className="material-icons-round">close</span>
                                                            </button>
                                                        </div>
                                                    );
                                                })}
                                                {(selectedCourse.students || []).length === 0 && (
                                                    <span className="no-users">No students enrolled</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="empty-state large">
                                <span className="material-icons-round">business</span>
                                <h3>Select a Department</h3>
                                <p>Choose a department from the sidebar to view and manage its courses</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Add Department Modal */}
                {showAddDept && (
                    <div className="modal-overlay" onClick={() => setShowAddDept(false)}>
                        <div className="modal-content" onClick={e => e.stopPropagation()}>
                            <h3>Add New Department</h3>
                            <form onSubmit={createDepartment}>
                                <div className="form-group">
                                    <label>Department Name</label>
                                    <input 
                                        type="text" 
                                        value={newDept.name}
                                        onChange={e => setNewDept({...newDept, name: e.target.value})}
                                        required
                                        placeholder="e.g., Computer Science"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Department Code</label>
                                    <input 
                                        type="text" 
                                        value={newDept.code}
                                        onChange={e => setNewDept({...newDept, code: e.target.value})}
                                        required
                                        placeholder="e.g., CS"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Description</label>
                                    <textarea 
                                        value={newDept.description}
                                        onChange={e => setNewDept({...newDept, description: e.target.value})}
                                        placeholder="Optional description..."
                                        rows="3"
                                    />
                                </div>
                                <div className="modal-actions">
                                    <button type="button" className="btn-secondary" onClick={() => setShowAddDept(false)}>Cancel</button>
                                    <button type="submit" className="btn-primary">Create Department</button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
