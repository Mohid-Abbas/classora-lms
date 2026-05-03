import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../../components/DashboardLayout";
import { apiClient } from "../../api/client";
import "./CreateCoursePage.css";

export default function CreateCoursePage() {
    const navigate = useNavigate();
    const [user] = useState(JSON.parse(localStorage.getItem("current_user") || "{}"));
    const [teachers, setTeachers] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [currentStep, setCurrentStep] = useState(1);
    const totalSteps = 4;

    const [formData, setFormData] = useState({
        name: "",
        code: "",
        department: "",
        semester: "Fall",
        academic_year: "2025-2026",
        section: "A",
        description: "",
        credits: "",
        duration_weeks: 16,
        max_students: "",
        is_published: false,
        assigned_teachers: [],
    });

    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState({ type: "", text: "" });

    useEffect(() => {
        // Fetch teachers
        apiClient.get(`/api/users/?role=TEACHER&institute=${user.institute_id}`)
            .then(res => {
                const data = Array.isArray(res.data) ? res.data : (res.data.results || []);
                setTeachers(data);
            })
            .catch(err => console.error("Error fetching teachers", err));

        // Fetch departments
        apiClient.get(`/api/lms/departments/`)
            .then(res => {
                const data = Array.isArray(res.data) ? res.data : (res.data.results || []);
                setDepartments(data);
            })
            .catch(err => console.error("Error fetching departments", err));
    }, [user.institute_id]);

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === "checkbox" ? checked : value
        }));
    };

    const handleTeacherToggle = (teacherId) => {
        setFormData(prev => {
            const alreadyAssigned = prev.assigned_teachers.includes(teacherId);
            const newList = alreadyAssigned
                ? prev.assigned_teachers.filter(id => id !== teacherId)
                : [...prev.assigned_teachers, teacherId];
            return { ...prev, assigned_teachers: newList };
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setMessage({ type: "", text: "" });

        try {
            const response = await apiClient.post("/api/lms/courses/", {
                ...formData,
                institute: user.institute_id,
                assigned_teachers: formData.assigned_teachers
            });
            
            if (response.data.done) {
                setMessage({ type: "success", text: "Course created successfully!" });
                setFormData({
                    name: "", code: "", department: "", semester: "Fall", academic_year: "2025-2026", section: "A",
                    description: "", credits: "", duration_weeks: 16, max_students: "",
                    is_published: false, assigned_teachers: []
                });
                setTimeout(() => navigate('/courses'), 2000);
            } else {
                setMessage({ type: "error", text: "Course creation incomplete. Please check all steps." });
            }
        } catch (err) {
            console.error("Course creation error:", err);
            console.error("Error response:", err.response?.data);
            console.error("Error status:", err.response?.status);
            
            if (err.response?.data?.step_errors) {
                const stepErrors = err.response.data.step_errors;
                const firstErrorStep = Object.keys(stepErrors)[0];
                setCurrentStep(parseInt(firstErrorStep));
                setMessage({ 
                    type: "error", 
                    text: `Step ${firstErrorStep}: ${Object.values(stepErrors[firstErrorStep])[0]}` 
                });
            } else if (err.response?.data) {
                // Show actual error from backend
                const errorData = err.response.data;
                let errorMessage = "Failed to create course. ";
                
                if (errorData.detail) {
                    errorMessage += errorData.detail;
                } else if (errorData.non_field_errors) {
                    errorMessage += errorData.non_field_errors.join(", ");
                } else {
                    errorMessage += JSON.stringify(errorData);
                }
                
                setMessage({ type: "error", text: errorMessage });
            } else {
                setMessage({ type: "error", text: "Failed to create course. Check your inputs." });
            }
        } finally {
            setSubmitting(false);
        }
    };

    const steps = [
        { num: 1, title: "Basic Info", icon: "info" },
        { num: 2, title: "Schedule", icon: "calendar_today" },
        { num: 3, title: "Teachers", icon: "person_add" },
        { num: 4, title: "Settings", icon: "settings" }
    ];

    const validateCurrentStep = () => {
        switch(currentStep) {
            case 1:
                return formData.name.trim() !== '' && 
                       formData.code.trim() !== '' && 
                       formData.department !== '';
            case 2:
                return formData.semester !== '' && 
                       formData.academic_year !== '' && 
                       formData.section !== '';
            case 3:
                return formData.assigned_teachers.length > 0;
            case 4:
                const credits = parseInt(formData.credits);
                const maxStudents = parseInt(formData.max_students);
                return !isNaN(credits) && credits > 0 && !isNaN(maxStudents) && maxStudents > 0 && typeof formData.is_published === 'boolean';
            default:
                return false;
        }
    };

    const nextStep = () => {
        if (validateCurrentStep()) {
            setCurrentStep(s => Math.min(s + 1, totalSteps));
        } else {
            setMessage({ type: "error", text: "Please fill all required fields before proceeding." });
        }
    };
    const prevStep = () => setCurrentStep(s => Math.max(s - 1, 1));

    const renderStep = () => {
        switch(currentStep) {
            case 1:
                return (
                    <div className="step-content">
                        <h3 className="step-title">Course Information</h3>
                        <div className="form-grid">
                            <div className="form-field full-width">
                                <label>Course Name *</label>
                                <input 
                                    name="name" 
                                    placeholder="e.g., Introduction to Computer Science" 
                                    value={formData.name} 
                                    onChange={handleInputChange} 
                                    required 
                                />
                            </div>
                            <div className="form-field">
                                <label>Course Code *</label>
                                <input 
                                    name="code" 
                                    placeholder="e.g., CS101" 
                                    value={formData.code} 
                                    onChange={handleInputChange} 
                                    required 
                                />
                            </div>
                            <div className="form-field">
                                <label>Department *</label>
                                <select name="department" value={formData.department} onChange={handleInputChange} required>
                                    <option value="">Select Department</option>
                                    {departments.map(d => (
                                        <option key={d.id} value={d.id}>{d.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-field full-width">
                                <label>Description</label>
                                <textarea 
                                    name="description" 
                                    placeholder="Course overview, learning objectives, prerequisites..." 
                                    value={formData.description} 
                                    onChange={handleInputChange}
                                    rows="4"
                                />
                            </div>
                        </div>
                    </div>
                );
            case 2:
                return (
                    <div className="step-content">
                        <h3 className="step-title">Schedule & Section</h3>
                        <div className="form-grid">
                            <div className="form-field">
                                <label>Semester *</label>
                                <select name="semester" value={formData.semester} onChange={handleInputChange}>
                                    <option value="Fall">Fall</option>
                                    <option value="Spring">Spring</option>
                                    <option value="Summer">Summer</option>
                                    <option value="Winter">Winter</option>
                                </select>
                            </div>
                            <div className="form-field">
                                <label>Academic Year *</label>
                                <input 
                                    name="academic_year" 
                                    placeholder="e.g., 2025-2026" 
                                    value={formData.academic_year} 
                                    onChange={handleInputChange} 
                                    required 
                                />
                            </div>
                            <div className="form-field">
                                <label>Section *</label>
                                <input 
                                    name="section" 
                                    placeholder="e.g., A, B, C" 
                                    value={formData.section} 
                                    onChange={handleInputChange} 
                                    required 
                                />
                            </div>
                            <div className="form-field">
                                <label>Duration (Weeks)</label>
                                <input type="number" name="duration_weeks" value={formData.duration_weeks} onChange={handleInputChange} />
                            </div>
                        </div>
                    </div>
                );
            case 3:
                return (
                    <div className="step-content">
                        <h3 className="step-title">Assign Teachers</h3>
                        <p className="step-subtitle">Select teachers to assign to this course</p>
                        <div className="teachers-selection">
                            {teachers.map(t => (
                                <div 
                                    key={t.id} 
                                    className={`teacher-select-card ${formData.assigned_teachers.includes(t.id) ? 'selected' : ''}`}
                                    onClick={() => handleTeacherToggle(t.id)}
                                >
                                    <div className="teacher-select-avatar">
                                        <span className="material-icons-round">person</span>
                                    </div>
                                    <div className="teacher-select-info">
                                        <div className="teacher-select-name">{t.full_name}</div>
                                        <div className="teacher-select-email">{t.email}</div>
                                    </div>
                                    <div className="teacher-select-check">
                                        <span className="material-icons-round">
                                            {formData.assigned_teachers.includes(t.id) ? 'check_circle' : 'radio_button_unchecked'}
                                        </span>
                                    </div>
                                </div>
                            ))}
                            {teachers.length === 0 && (
                                <div className="empty-teachers">No teachers available. Add teachers first.</div>
                            )}
                        </div>
                    </div>
                );
            case 4:
                return (
                    <div className="step-content">
                        <h3 className="step-title">Course Settings</h3>
                        <p className="step-subtitle">Configure course credits, capacity, and visibility</p>
                        <div className="form-grid">
                            <div className="form-field">
                                <label>Credits *</label>
                                <input 
                                    type="number" 
                                    name="credits" 
                                    value={formData.credits} 
                                    onChange={handleInputChange}
                                    min="1"
                                    max="10"
                                    placeholder="e.g., 3"
                                    required 
                                />
                                <small>Number of credit hours for this course</small>
                            </div>
                            <div className="form-field">
                                <label>Maximum Students *</label>
                                <input 
                                    type="number" 
                                    name="max_students" 
                                    value={formData.max_students} 
                                    onChange={handleInputChange}
                                    min="1"
                                    max="500"
                                    placeholder="e.g., 50"
                                    required 
                                />
                                <small>Maximum number of students that can enroll</small>
                            </div>
                        </div>
                        <div className="publish-toggle">
                            <label className="toggle-label">
                                <input
                                    type="checkbox"
                                    name="is_published"
                                    checked={formData.is_published}
                                    onChange={handleInputChange}
                                />
                                <span className="toggle-switch"></span>
                                <span className="toggle-text">
                                    <span className="material-icons-round">{formData.is_published ? 'visibility' : 'visibility_off'}</span>
                                    {formData.is_published ? "Published (visible to students)" : "Draft (not visible to students)"}
                                </span>
                            </label>
                            <small>Choose whether students can see this course immediately</small>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <DashboardLayout user={user}>
            <div className="create-course-container">
                <div className="create-course-header">
                    <h1>Create New Course</h1>
                    <p>Set up a new course for your institute</p>
                </div>

                {message.text && (
                    <div className={`message-banner ${message.type}`}>
                        {message.text}
                        <button onClick={() => setMessage({ type: "", text: "" })}>×</button>
                    </div>
                )}

                {/* Progress Steps */}
                <div className="steps-indicator">
                    {steps.map(step => (
                        <div 
                            key={step.num} 
                            className={`step-item ${currentStep === step.num ? 'active' : ''} ${currentStep > step.num ? 'completed' : ''}`}
                        >
                            <div className="step-icon">
                                <span className="material-icons-round">
                                    {currentStep > step.num ? 'check' : step.icon}
                                </span>
                            </div>
                            <div className="step-text">
                                <span className="step-number">Step {step.num}</span>
                                <span className="step-title">{step.title}</span>
                            </div>
                        </div>
                    ))}
                </div>

                <form onSubmit={handleSubmit} className="course-wizard-form">
                    {/* Step Content */}
                    {renderStep()}

                    {/* Navigation Buttons */}
                    <div className="wizard-navigation">
                        <button 
                            type="button" 
                            className="nav-btn prev"
                            onClick={prevStep}
                            disabled={currentStep === 1}
                        >
                            <span className="material-icons-round">arrow_back</span>
                            Previous
                        </button>
                        
                        {currentStep < totalSteps ? (
                            <button 
                                type="button" 
                                className="nav-btn next"
                                onClick={nextStep}
                                disabled={!validateCurrentStep()}
                            >
                                Next
                                <span className="material-icons-round">arrow_forward</span>
                            </button>
                        ) : (
                            <button 
                                type="submit" 
                                className="nav-btn submit"
                                disabled={submitting || !validateCurrentStep()}
                            >
                                {submitting ? (
                                    <>
                                        <span className="material-icons-round spin">sync</span>
                                        Creating...
                                    </>
                                ) : validateCurrentStep() ? (
                                    <>
                                        <span className="material-icons-round">check</span>
                                        Create Course
                                    </>
                                ) : (
                                    <>
                                        <span className="material-icons-round">warning</span>
                                        Complete Required Fields
                                    </>
                                )}
                            </button>
                        )}
                    </div>
                </form>

                {/* Live Preview Card */}
                <div className="course-preview-card">
                    <div className="preview-header">
                        <div className="preview-icon">
                            <span className="material-icons-round">school</span>
                        </div>
                        <div className="preview-info">
                            <h4>{formData.name || "Course Name"}</h4>
                            <p>{formData.code || "CODE101"} • {formData.semester} {formData.academic_year}</p>
                        </div>
                    </div>
                    <div className="preview-details">
                        <div className="preview-item">
                            <span className="material-icons-round">business</span>
                            <span>{departments.find(d => d.id === parseInt(formData.department))?.name || "No Department"}</span>
                        </div>
                        <div className="preview-item">
                            <span className="material-icons-round">group</span>
                            <span>Section {formData.section}</span>
                        </div>
                        <div className="preview-item">
                            <span className="material-icons-round">person</span>
                            <span>{formData.assigned_teachers.length} Teachers</span>
                        </div>
                        <div className="preview-item">
                            <span className="material-icons-round">schedule</span>
                            <span>{formData.duration_weeks} Weeks • {formData.credits} Credits</span>
                        </div>
                    </div>
                    <div className={`preview-status ${formData.is_published ? 'published' : 'draft'}`}>
                        <span className="material-icons-round">
                            {formData.is_published ? 'visibility' : 'visibility_off'}
                        </span>
                        {formData.is_published ? "Published" : "Draft"}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
