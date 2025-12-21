-- =====================================================
-- Cellular Network Database Schema
-- Connect System - Exercise 1
-- =====================================================

-- 1. CellularProviders (Parent table for all providers)
CREATE TABLE CellularProviders (
    ProviderID INT PRIMARY KEY,
    ProviderName NVARCHAR(100) NOT NULL,
    Email NVARCHAR(100),
    Password NVARCHAR(100),
    EstablishmentDate DATE
);

-- 2. TrafficProvider (MVNO - no infrastructure)
CREATE TABLE TrafficProvider (
    ProviderID INT PRIMARY KEY,
    FOREIGN KEY (ProviderID) REFERENCES CellularProviders(ProviderID)
);

-- 3. InfrastructureProvider (MNO - owns network)
CREATE TABLE InfrastructureProvider (
    ProviderID INT PRIMARY KEY,
    FOREIGN KEY (ProviderID) REFERENCES CellularProviders(ProviderID)
);

-- 4. CentralExchange
CREATE TABLE CentralExchange (
    UniquePrefix NVARCHAR(10) PRIMARY KEY,
    ExchangeName NVARCHAR(100) NOT NULL,
    SupportedTechnology NVARCHAR(200),
    SupportStartDate DATE,
    ProviderID INT NOT NULL,
    FOREIGN KEY (ProviderID) REFERENCES InfrastructureProvider(ProviderID)
);

-- 5. BaseStation
CREATE TABLE BaseStation (
    StationID INT PRIMARY KEY,
    StationName NVARCHAR(100) NOT NULL,
    HeightMeters FLOAT,
    LocationX FLOAT,
    LocationY FLOAT,
    RangeMeters INT CHECK (RangeMeters BETWEEN 0 AND 500),
    AntennaCount TINYINT CHECK (AntennaCount BETWEEN 1 AND 5),
    EstablishmentDate DATE,
    ExchangePrefix NVARCHAR(10),
    FOREIGN KEY (ExchangePrefix) REFERENCES CentralExchange(UniquePrefix)
);

-- 6. SIMCard
CREATE TABLE SIMCard (
    IMSI CHAR(15) PRIMARY KEY,
    ProviderID INT NOT NULL,
    FOREIGN KEY (ProviderID) REFERENCES CellularProviders(ProviderID)
);

-- 7. CellularDevice
CREATE TABLE CellularDevice (
    IMEI CHAR(15) PRIMARY KEY,
    ManufacturingContinent NVARCHAR(50) CHECK (ManufacturingContinent IN ('Antarctica', 'Oceania', 'South America', 'North America', 'Africa', 'Asia', 'Europe')),
    SupportedTechnology NVARCHAR(200)
);

-- 8. AttachedTo (SIM attached to Device)
CREATE TABLE AttachedTo (
    IMSI CHAR(15) NOT NULL,
    IMEI CHAR(15) NOT NULL,
    FirstAttachmentTime DATE NOT NULL,
    PRIMARY KEY (IMSI, IMEI),
    FOREIGN KEY (IMSI) REFERENCES SIMCard(IMSI),
    FOREIGN KEY (IMEI) REFERENCES CellularDevice(IMEI)
);

-- 9. PhoneCall
CREATE TABLE PhoneCall (
    IMSI CHAR(15) NOT NULL,
    IMEI CHAR(15) NOT NULL,
    SequenceOrder INT NOT NULL,
    StationID INT,
    ExecutionTime DATE NOT NULL,
    LocationTime DATE,
    EstimatedLocationX FLOAT,
    EstimatedLocationY FLOAT,
    PRIMARY KEY (IMSI, IMEI, SequenceOrder),
    FOREIGN KEY (IMSI) REFERENCES SIMCard(IMSI),
    FOREIGN KEY (IMEI) REFERENCES CellularDevice(IMEI),
    FOREIGN KEY (StationID) REFERENCES BaseStation(StationID)
);
