import React, { useState, useEffect } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiClient } from "../api/client";
import "./AnnouncementsPage.css";

export default function AnnouncementsPage() {
    const user = JSON.parse(localStorage.getItem("current_user") || "{}");
    const [announcements, setAnnouncements] = useState([]);
    const [courses, setCourses] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(true);

    const [formData, setFormData] = useState({
        title: "",
        content: "",
        target_role: "ALL",
        course: "",
        department: ""
    });
    const [selectedImage, setSelectedImage] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [commentTexts, setCommentTexts] = useState({});
    const [editingComment, setEditingComment] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [expandedComments, setExpandedComments] = useState({}); // Track which announcements show comments

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [annRes, crsRes, deptRes] = await Promise.all([
                apiClient.get("/api/lms/announcements/"),
                apiClient.get("/api/lms/courses/"),
                user.role === "ADMIN" ? apiClient.get("/api/lms/departments/") : Promise.resolve({ data: [] })
            ]);
            setAnnouncements(Array.isArray(annRes.data) ? annRes.data : (annRes.data.results || []));
            setCourses(Array.isArray(crsRes.data) ? crsRes.data : (crsRes.data.results || []));
            setDepartments(Array.isArray(deptRes.data) ? deptRes.data : (deptRes.data.results || []));
        } catch (err) {
            console.error("Failed fetching data", err);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleImageChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedImage(e.target.files[0]);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            const data = new FormData();
            data.append("title", formData.title);
            data.append("content", formData.content);
            data.append("target_role", formData.target_role);
            if (formData.course) data.append("course", formData.course);
            if (formData.department && user.role === "ADMIN") data.append("department", formData.department);
            if (selectedImage) data.append("image", selectedImage);

            await apiClient.post("/api/lms/announcements/", data, {
                headers: { "Content-Type": "multipart/form-data" }
            });
            
            setFormData({ title: "", content: "", target_role: "ALL", course: "", department: "" });
            setSelectedImage(null);
            setShowModal(false);
            fetchData();
        } catch (err) {
            alert("Failed to post announcement. " + JSON.stringify(err.response?.data || ""));
        } finally {
            setSubmitting(false);
        }
    };

    const closeModal = () => {
        setShowModal(false);
        setFormData({ title: "", content: "", target_role: "ALL", course: "", department: "" });
        setSelectedImage(null);
    };

    const toggleComments = (annId) => {
        setExpandedComments({ ...expandedComments, [annId]: !expandedComments[annId] });
    };

    const postComment = async (announcementId) => {
        const txt = commentTexts[announcementId];
        if (!txt || !txt.trim()) return;
        try {
            await apiClient.post("/api/lms/announcement-comments/", {
                announcement: announcementId,
                content: txt
            });
            setCommentTexts({ ...commentTexts, [announcementId]: "" });
            fetchData();
        } catch(err) {
            const msg = err.response?.data?.detail || err.response?.data?.content?.[0] || "Server error";
            alert(`Failed to post comment: ${msg}`);
        }
    };

    const deleteAnnouncement = async (id) => {
        if (!window.confirm("Are you sure you want to delete this announcement?")) return;
        try {
            await apiClient.delete(`/api/lms/announcements/${id}/`);
            fetchData();
        } catch(err) {
            alert("Failed to delete announcement.");
        }
    };

    const deleteComment = async (id) => {
        if (!window.confirm("Delete your comment?")) return;
        try {
            await apiClient.delete(`/api/lms/announcement-comments/${id}/`);
            fetchData();
        } catch(err) {
            const msg = err.response?.data?.detail || "Failed to delete comment.";
            alert(msg);
        }
    };

    const startEditComment = (cmt) => {
        setEditingComment({ id: cmt.id, content: cmt.content });
    };

    const cancelEditComment = () => {
        setEditingComment(null);
    };

    const updateComment = async () => {
        if (!editingComment || !editingComment.content.trim()) return;
        try {
            await apiClient.patch(`/api/lms/announcement-comments/${editingComment.id}/`, {
                content: editingComment.content
            });
            setEditingComment(null);
            fetchData();
        } catch(err) {
            const msg = err.response?.data?.detail || "Failed to update comment.";
            alert(msg);
        }
    };

    const canCreate = user.role !== "STUDENT" || courses.length > 0;

    return (
        <DashboardLayout user={user}>
            <div className="ann-page-container">
                <div className="ann-header-bar">
                    <div className="ann-header-title">
                        <h1>Announcements</h1>
                        <p>Manage institute-wide communications</p>
                    </div>
                    {canCreate && (
                        <button className="ann-new-btn" onClick={() => setShowModal(true)}>
                            <span className="material-icons-round">add</span>
                            New Announcement
                        </button>
                    )}
                </div>

                {/* Create Modal */}
                {showModal && (
                    <div className="ann-modal-overlay" onClick={closeModal}>
                        <div className="ann-modal" onClick={(e) => e.stopPropagation()}>
                            <div className="ann-modal-header">
                                <h3><span className="material-icons-round">campaign</span> New Announcement</h3>
                                <button className="ann-modal-close" onClick={closeModal}>
                                    <span className="material-icons-round">close</span>
                                </button>
                            </div>
                            <form onSubmit={handleSubmit} className="ann-modal-form">
                                <div className="ann-form-group">
                                    <label>Title</label>
                                    <input type="text" name="title" value={formData.title} onChange={handleInputChange} required placeholder="Enter announcement title..." />
                                </div>

                                <div className="ann-form-row">
                                    <div className="ann-form-group">
                                        <label>Target</label>
                                        <select name="target_role" value={formData.target_role} onChange={handleInputChange}>
                                            <option value="ALL">Everyone</option>
                                            <option value="STUDENT">Students Only</option>
                                            <option value="TEACHER">Teachers Only</option>
                                        </select>
                                    </div>
                                    {user.role === "ADMIN" && (
                                        <div className="ann-form-group">
                                            <label>Department</label>
                                            <select name="department" value={formData.department} onChange={handleInputChange}>
                                                <option value="">All Departments</option>
                                                {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                                            </select>
                                        </div>
                                    )}
                                </div>

                                <div className="ann-form-group">
                                    <label>Course (Optional)</label>
                                    <select name="course" value={formData.course} onChange={handleInputChange}>
                                        <option value="">All Courses</option>
                                        {courses
                                            .filter(c => !formData.department || c.department === parseInt(formData.department))
                                            .map(c => <option key={c.id} value={c.id}>{c.code}: {c.name}</option>)
                                        }
                                    </select>
                                </div>

                                <div className="ann-form-group">
                                    <label>Message</label>
                                    <textarea name="content" value={formData.content} onChange={handleInputChange} required placeholder="Write your announcement message..." rows={5} />
                                </div>

                                <div className="ann-form-group">
                                    <label>Attachment</label>
                                    <div className="ann-file-input">
                                        <input type="file" accept="image/*" onChange={handleImageChange} id="ann-file" />
                                        <label htmlFor="ann-file" className={selectedImage ? 'has-file' : ''}>
                                            <span className="material-icons-round">image</span>
                                            {selectedImage ? selectedImage.name : "Choose an image..."}
                                        </label>
                                    </div>
                                </div>

                                <div className="ann-modal-actions">
                                    <button type="button" className="ann-btn-secondary" onClick={closeModal}>Cancel</button>
                                    <button type="submit" className="ann-btn-primary" disabled={submitting}>
                                        {submitting ? "Publishing..." : "Post Announcement"}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {/* Announcements List */}
                <div className="ann-list">
                    {loading && <div className="ann-empty"><p>Loading...</p></div>}
                    
                    {!loading && announcements.length === 0 && (
                        <div className="ann-empty">
                            <span className="material-icons-round">notifications_off</span>
                            <p>No announcements yet</p>
                        </div>
                    )}

                    {!loading && announcements.map(ann => {
                        const d = new Date(ann.created_at);
                        const commentCount = ann.comments?.length || 0;
                        const showComments = expandedComments[ann.id];
                        
                        return (
                            <div key={ann.id} className="ann-bar">
                                <div className="ann-bar-main">
                                    <div className="ann-bar-icon">
                                        <span className="material-icons-round">campaign</span>
                                    </div>
                                    <div className="ann-bar-content">
                                        <div className="ann-bar-header">
                                            <h4 className="ann-bar-title">{ann.title}</h4>
                                            <div className="ann-bar-meta">
                                                <span className="ann-bar-author">{ann.author_name}</span>
                                                <span className="ann-bar-dot">•</span>
                                                <span className="ann-bar-date">{d.toLocaleDateString()}</span>
                                                <span className="ann-bar-time">{d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                                            </div>
                                        </div>
                                        <p className="ann-bar-text">{ann.content}</p>
                                        
                                        {ann.image_url && (
                                            <div className="ann-bar-image">
                                                <img src={ann.image_url} alt="" />
                                            </div>
                                        )}

                                        <div className="ann-bar-footer">
                                            <button 
                                                className="ann-bar-comment-toggle"
                                                onClick={() => toggleComments(ann.id)}
                                            >
                                                <span className="material-icons-round">chat_bubble_outline</span>
                                                {commentCount > 0 ? `${commentCount} Comments` : "No comments"}
                                                <span className="material-icons-round expand-icon">
                                                    {showComments ? 'expand_less' : 'expand_more'}
                                                </span>
                                            </button>
                                            
                                            {(user.role === 'ADMIN' || user.id === ann.author) && (
                                                <button 
                                                    className="ann-bar-delete"
                                                    onClick={() => deleteAnnouncement(ann.id)}
                                                >
                                                    <span className="material-icons-round">delete_outline</span>
                                                    Delete
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Expandable Comments Section */}
                                {showComments && (
                                    <div className="ann-bar-comments">
                                        {commentCount === 0 ? (
                                            <div className="ann-no-comments">No comments yet. Be the first to comment!</div>
                                        ) : (
                                            <div className="ann-comments-list">
                                                {ann.comments.map(cmt => (
                                                    <div key={cmt.id} className="ann-comment-item">
                                                        <div className="ann-comment-avatar">
                                                            <span className="material-icons-round">account_circle</span>
                                                        </div>
                                                        <div className="ann-comment-body">
                                                            {editingComment && editingComment.id === cmt.id ? (
                                                                <div className="ann-comment-edit">
                                                                    <input
                                                                        value={editingComment.content}
                                                                        onChange={e => setEditingComment({ ...editingComment, content: e.target.value })}
                                                                        onKeyDown={e => {
                                                                            if (e.key === 'Enter') updateComment();
                                                                            if (e.key === 'Escape') cancelEditComment();
                                                                        }}
                                                                        autoFocus
                                                                    />
                                                                    <button onClick={updateComment}><span className="material-icons-round">check</span></button>
                                                                    <button onClick={cancelEditComment}><span className="material-icons-round">close</span></button>
                                                                </div>
                                                            ) : (
                                                                <>
                                                                    <div className="ann-comment-header">
                                                                        <span className="ann-comment-author">{cmt.user_name}</span>
                                                                        <span className="ann-comment-role">{cmt.user_role}</span>
                                                                        {(user.role === 'ADMIN' || user.id === cmt.user) && (
                                                                            <div className="ann-comment-actions">
                                                                                <button onClick={() => startEditComment(cmt)} title="Edit">
                                                                                    <span className="material-icons-round">edit</span>
                                                                                </button>
                                                                                <button onClick={() => deleteComment(cmt.id)} title="Delete">
                                                                                    <span className="material-icons-round">delete</span>
                                                                                </button>
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                    <div className="ann-comment-text">{cmt.content}</div>
                                                                </>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                        
                                        {/* Comment Input */}
                                        <div className="ann-comment-input-row">
                                            <input
                                                type="text"
                                                placeholder="Add a comment..."
                                                value={commentTexts[ann.id] || ""}
                                                onChange={e => setCommentTexts({ ...commentTexts, [ann.id]: e.target.value })}
                                                onKeyDown={e => e.key === 'Enter' && postComment(ann.id)}
                                            />
                                            <button onClick={() => postComment(ann.id)} disabled={!commentTexts[ann.id]?.trim()}>
                                                <span className="material-icons-round">send</span>
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </DashboardLayout>
    );
}
