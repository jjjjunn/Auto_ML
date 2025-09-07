from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Social Login IDs
    kakao_id = Column(String, unique=True, nullable=True)
    google_id = Column(String, unique=True, nullable=True)
    naver_id = Column(String, unique=True, nullable=True)

    # For Subscription
    subscription_plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    subscription_plan = relationship("SubscriptionPlan", back_populates="users")
    
    # Relationships
    projects = relationship("UserProjectAssociation", back_populates="user")
    data_sources = relationship("DataSource", back_populates="owner")
    automl_runs = relationship("AutoMLRun", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    email_share_logs = relationship("EmailShareLog", back_populates="sender")
    activity_logs = relationship("ActivityLog", back_populates="user")
    user_subscriptions = relationship("UserSubscription", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    members = relationship("UserProjectAssociation", back_populates="project")
    data_sources = relationship("DataSource", back_populates="project")
    automl_runs = relationship("AutoMLRun", back_populates="project")
    visualization_charts = relationship("VisualizationChart", back_populates="project")


class UserProjectAssociation(Base):
    __tablename__ = "user_project_association"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    role = Column(String, default="member") # e.g., "owner", "member"

    user = relationship("User", back_populates="projects")
    project = relationship("Project", back_populates="members")


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String)
    file_path = Column(String, unique=True, index=True) # Path to the parquet file
    original_file_name = Column(String, nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True) # Optional: link to project

    owner = relationship("User", back_populates="data_sources")
    project = relationship("Project", back_populates="data_sources")
    automl_runs = relationship("AutoMLRun", back_populates="data_source")


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    model_type = Column(String) # e.g., Classification, Regression, Clustering
    model_path = Column(String, unique=True, index=True) # Path to the joblib model file
    trained_at = Column(DateTime, server_default=func.now())
    metrics = Column(Text, nullable=True) # Store metrics as JSON string
    target_column = Column(String, nullable=True)
    features = Column(Text, nullable=True) # Store features as JSON string

    automl_runs = relationship("AutoMLRun", back_populates="ml_model")


class AutoMLRun(Base):
    __tablename__ = "automl_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"))
    ml_model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=True) # Link to trained model
    run_at = Column(DateTime, server_default=func.now())
    status = Column(String, default="completed") # e.g., "pending", "running", "completed", "failed"
    recommendations = Column(Text, nullable=True) # Store recommendations as JSON string
    run_details = Column(Text, nullable=True) # Store other run details as JSON string

    user = relationship("User", back_populates="automl_runs")
    project = relationship("Project", back_populates="automl_runs")
    data_source = relationship("DataSource", back_populates="automl_runs")
    ml_model = relationship("MLModel", back_populates="automl_runs")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    sender = Column(String) # "user" or "ai"
    message = Column(Text)
    timestamp = Column(DateTime, server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")


class VisualizationChart(Base):
    __tablename__ = "visualization_charts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    chart_type = Column(String) # e.g., "bar", "line", "scatter"
    image_path = Column(String, nullable=True) # Path to saved chart image
    data_source_id = Column(Integer, ForeignKey("data_sources.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    data_source = relationship("DataSource")
    project = relationship("Project", back_populates="visualization_charts")
    email_share_logs = relationship("EmailShareLog", back_populates="chart")


class EmailShareLog(Base):
    __tablename__ = "email_share_logs"

    id = Column(Integer, primary_key=True, index=True)
    chart_id = Column(Integer, ForeignKey("visualization_charts.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    recipient_email = Column(String)
    sent_at = Column(DateTime, server_default=func.now())
    status = Column(String) # e.g., "success", "failed"

    chart = relationship("VisualizationChart", back_populates="email_share_logs")
    sender = relationship("User", back_populates="email_share_logs")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True) # e.g., "Free", "Basic", "Premium"
    price = Column(Float)
    features = Column(Text) # JSON string of features
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    users = relationship("User", back_populates="subscription_plan")
    user_subscriptions = relationship("UserSubscription", back_populates="subscription_plan")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    start_date = Column(DateTime, server_default=func.now())
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="user_subscriptions")
    subscription_plan = relationship("SubscriptionPlan", back_populates="user_subscriptions")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Nullable for system activities
    activity_type = Column(String) # e.g., "login", "file_upload", "model_train", "chart_view"
    description = Column(Text)
    timestamp = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="activity_logs")
