import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

interface PivotData {
    headers: string[];
    rows: { [key: string]: any }[];
}

const SummaryView: React.FC = () => {
    const [summaryData, setSummaryData] = useState<PivotData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchSummary = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const response = await axios.get<PivotData>(`${API_BASE_URL}/api/ratings/summary`);
                setSummaryData(response.data);
            } catch (err) {
                setError('Failed to load summary data.');
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchSummary();
    }, []);

    const handleDownloadCsv = () => {
        if (!summaryData) return;

        const { headers, rows } = summaryData;
        
        const csvHeader = headers.join(',') + '\n';

        const csvRows = rows.map(row => {
            return headers.map(header => {
                const value = row[header];
                if (value === null || value === undefined) {
                    return '';
                }
                const stringValue = String(value);
                // Escape double quotes by doubling them, and wrap the whole thing in quotes
                const escapedValue = stringValue.replace(/"/g, '""');
                return `"${escapedValue}"`;
            }).join(',');
        }).join('\n');

        const csvContent = csvHeader + csvRows;

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        if (link.href) {
            URL.revokeObjectURL(link.href);
        }
        link.href = URL.createObjectURL(blob);
        link.download = 'ratings_summary.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    if (isLoading) {
        return <div className="d-flex justify-content-center mt-5"><div className="spinner-border" role="status"><span className="visually-hidden">Loading...</span></div></div>;
    }

    if (error) {
        return <div className="alert alert-danger mt-4">{error}</div>;
    }

    if (!summaryData || summaryData.rows.length === 0) {
        return <div className="alert alert-info mt-4">No rating data available.</div>;
    }

    return (
        <div className="container-fluid mt-4">
            <div className="d-flex justify-content-between align-items-center mb-3">
                <h1>Ratings Summary</h1>
                <button className="btn btn-primary" onClick={handleDownloadCsv}>
                    Download CSV
                </button>
            </div>
            <div className="table-responsive">
                <table className="table table-striped table-bordered table-hover table-sm">
                    <thead className="table-dark">
                        <tr>
                            {summaryData.headers.map(header => <th key={header} scope="col" style={{whiteSpace: 'nowrap'}}>{header}</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {summaryData.rows.map((row, index) => (
                            <tr key={index}>
                                {summaryData.headers.map(header => {
                                    const value = row[header];
                                    let displayValue = value === null || value === undefined ? '-' : value;

                                    // For the Filename column, only show the base name
                                    if (header === 'Filename' && typeof value === 'string') {
                                        displayValue = value.split('/').pop() || value;
                                    }

                                    return <td key={header}>{displayValue}</td>;
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default SummaryView;
