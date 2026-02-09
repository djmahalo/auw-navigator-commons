-- Create schema objects for AUW Navigator 211 POC
-- Run in your Azure SQL DB

IF OBJECT_ID('dbo.QueueItem', 'U') IS NOT NULL DROP TABLE dbo.QueueItem;
IF OBJECT_ID('dbo.RuleResult', 'U') IS NOT NULL DROP TABLE dbo.RuleResult;
IF OBJECT_ID('dbo.Rule', 'U') IS NOT NULL DROP TABLE dbo.Rule;
IF OBJECT_ID('dbo.Intake', 'U') IS NOT NULL DROP TABLE dbo.Intake;
GO

CREATE TABLE dbo.Intake (
    IntakeId        INT IDENTITY(1,1) PRIMARY KEY,
    CreatedAt       DATETIME2(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    CallerId        NVARCHAR(100) NULL,
    Channel         NVARCHAR(50)  NOT NULL,
    DomainModule    NVARCHAR(100) NOT NULL,
    Priority        NVARCHAR(20)  NOT NULL DEFAULT 'Normal',
    Crisis          BIT           NOT NULL DEFAULT 0,
    Narrative       NVARCHAR(MAX) NULL,
    AttributesJson  NVARCHAR(MAX) NULL
);
GO

CREATE TABLE dbo.Rule (
    RuleId            INT IDENTITY(1,1) PRIMARY KEY,
    RuleName          NVARCHAR(200) NOT NULL,
    IsEnabled         BIT NOT NULL DEFAULT 1,
    PriorityOrder     INT NOT NULL DEFAULT 100,
    MatchJson         NVARCHAR(MAX) NOT NULL,
    Action            NVARCHAR(50) NOT NULL,
    ActionParamsJson  NVARCHAR(MAX) NULL
);
GO

CREATE TABLE dbo.RuleResult (
    RuleResultId   INT IDENTITY(1,1) PRIMARY KEY,
    EvaluatedAt    DATETIME2(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    IntakeId       INT NOT NULL,
    RuleId         INT NOT NULL,
    Action         NVARCHAR(50) NOT NULL,
    OutcomeJson    NVARCHAR(MAX) NULL,
    CONSTRAINT FK_RuleResult_Intake FOREIGN KEY (IntakeId) REFERENCES dbo.Intake(IntakeId),
    CONSTRAINT FK_RuleResult_Rule FOREIGN KEY (RuleId) REFERENCES dbo.Rule(RuleId)
);
GO

CREATE TABLE dbo.QueueItem (
    QueueItemId    INT IDENTITY(1,1) PRIMARY KEY,
    CreatedAt      DATETIME2(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    IntakeId       INT NOT NULL,
    QueueName      NVARCHAR(100) NOT NULL,
    Status         NVARCHAR(20) NOT NULL DEFAULT 'Open', -- Open|InProgress|Closed
    Reason         NVARCHAR(400) NULL,
    CONSTRAINT FK_QueueItem_Intake FOREIGN KEY (IntakeId) REFERENCES dbo.Intake(IntakeId)
);
GO

CREATE INDEX IX_Intake_CreatedAt ON dbo.Intake(CreatedAt DESC);
CREATE INDEX IX_QueueItem_QueueName ON dbo.QueueItem(QueueName, Status, CreatedAt DESC);
GO
