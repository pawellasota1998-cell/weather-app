USE [master];
GO


IF DB_ID(N'$(DB_NAME)') IS NULL
BEGIN
    CREATE DATABASE [$(DB_NAME)];
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.sql_logins
    WHERE [name] = N'$(DB_USER)'
)

BEGIN
    CREATE LOGIN [$(DB_USER)]
    WITH PASSWORD = N'$(DB_PASSWORD)',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
END;
ELSE
BEGIN
    ALTER LOGIN [$(DB_USER)]
    WITH PASSWORD = N'$(DB_PASSWORD)';
END;
GO


USE [$(DB_NAME)];
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.database_principals
    WHERE [name] = N'$(DB_USER)'
)

BEGIN
    CREATE USER [$(DB_USER)]
    FOR LOGIN [$(DB_USER)];
END;
GO
IF IS_ROLEMEMBER(N'db_owner', N'$(DB_USER)') <> 1
BEGIN
    ALTER ROLE [db_owner]
    ADD MEMBER [$(DB_USER)];
END;
GO