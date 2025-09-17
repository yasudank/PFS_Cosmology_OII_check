import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';
const PAGE_SIZE = 20;
const RATING_OPTIONS = [0, 1, 2];

// Types
interface ImageWithRating {
    id: number;
    filename: string;
    path: string;
    rating1: number | null;
    rating2: number | null;
}

interface PaginatedImageResponse {
    images: ImageWithRating[];
}

interface CountsResponse {
    total_images: number;
    unrated_images: number;
}

interface ImageRaterProps {
    userName: string;
}

interface RatingChanges {
    [key: number]: { rating1?: number; rating2?: number; };
}

const ImageRater: React.FC<ImageRaterProps> = ({ userName }) => {
    const { filename: filenameFromUrl } = useParams<{ filename: string }>();

    // Server state
    const [images, setImages] = useState<ImageWithRating[]>([]);
    const [totalImages, setTotalImages] = useState(0);
    const [unratedImages, setUnratedImages] = useState(0);
    
    // UI state
    const [currentPage, setCurrentPage] = useState(1);
    const [pageInput, setPageInput] = useState("1");
    const [filter, setFilter] = useState<'all' | 'unrated'>('all');
    const [searchInput, setSearchInput] = useState(filenameFromUrl ? decodeURIComponent(filenameFromUrl) : "");
    const [ratingChanges, setRatingChanges] = useState<RatingChanges>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const countForPagination = filter === 'all' ? totalImages : unratedImages;
    const totalPages = Math.ceil(countForPagination / PAGE_SIZE);

    const fetchCounts = useCallback(async () => {
        try {
            const params = { user_name: userName };
            const response = await axios.get<CountsResponse>(`${API_BASE_URL}/api/counts`, { params });
            setTotalImages(response.data.total_images);
            setUnratedImages(response.data.unrated_images);
        } catch (err) {
            console.error("Failed to load counts", err);
            setError("Could not load image counts.");
        }
    }, [userName]);

    const performSearch = useCallback(async (filenameToSearch: string) => {
        setError(null);
        try {
            const params = { user_name: userName, filter, filename: filenameToSearch, limit: PAGE_SIZE };
            const response = await axios.get<{ page: number }>(`${API_BASE_URL}/api/images/find`, { params });
            if (response.data.page !== currentPage) {
                setCurrentPage(response.data.page);
            } else {
                // If the image is already on the current page, just clear the error.
                // The loading state is handled by the main useEffect.
            }
        } catch (err: any) {
            if (axios.isAxiosError(err) && err.response) {
                setError(err.response.data.detail || 'Image not found.');
            } else {
                setError('An error occurred while searching.');
            }
            console.error(err);
        }
    }, [userName, filter, currentPage]);

    // Effect to trigger search when filenameFromUrl changes
    useEffect(() => {
        if (userName && filenameFromUrl) {
            const decodedFilename = decodeURIComponent(filenameFromUrl);
            setSearchInput(decodedFilename);
            performSearch(decodedFilename);
        }
    }, [userName, filenameFromUrl, performSearch]);

    // Main data fetching effect
    useEffect(() => {
        const fetchImages = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const params: any = { user_name: userName, filter, page: currentPage, limit: PAGE_SIZE };
                // If filenameFromUrl is present, it means we are coming from a direct link
                // and the performSearch effect should have already set the correct page.
                // We don't need to add filename to params here for general image fetching.
                const response = await axios.get<PaginatedImageResponse>(`${API_BASE_URL}/api/images`, { params });
                setImages(response.data.images);
                setRatingChanges({});
            } catch (err) {
                setError('Failed to load images. Please make sure the backend server is running.');
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };

        if (userName) {
            fetchImages();
        }
    }, [userName, currentPage, filter]);

    // Initial data load and refetch counts on filter change
    useEffect(() => {
        if (userName) {
            fetchCounts();
        }
        setCurrentPage(1);
    }, [userName, filter, fetchCounts]);

    // Sync page input with current page
    useEffect(() => {
        setPageInput(currentPage.toString());
    }, [currentPage]);

    const handlePageJump = () => {
        const pageNum = parseInt(pageInput, 10);
        if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= totalPages) {
            setCurrentPage(pageNum);
        } else {
            alert(`Please enter a valid page number between 1 and ${totalPages}.`);
            setPageInput(currentPage.toString());
        }
    };

    const handleRatingChange = (imageId: number, ratingName: 'rating1' | 'rating2', value: number) => {
        setRatingChanges(prev => ({ ...prev, [imageId]: { ...prev[imageId], [ratingName]: value } }));
    };

    const handleSubmitChanges = async () => {
        setIsSubmitting(true);
        setError(null);

        const changedImages = Object.entries(ratingChanges).filter(([_, r]) => r.rating1 !== undefined || r.rating2 !== undefined);
        const submissionPromises = changedImages.map(([imageIdStr, changes]) => {
            const imageId = Number(imageIdStr);
            const originalImage = images.find(img => img.id === imageId);
            const payload = { user_name: userName, rating1: changes.rating1 ?? originalImage?.rating1, rating2: changes.rating2 ?? originalImage?.rating2 };
            if (payload.rating1 === null || payload.rating2 === null) {
                return Promise.reject(new Error(`Image ${originalImage?.filename.split('/').pop()} must have both ratings selected.`));
            }
            return axios.post(`${API_BASE_URL}/api/images/${imageId}/rate`, payload);
        });

        try {
            await Promise.all(submissionPromises);
            // Refetch counts and current page data
            await fetchCounts();
            const params = { user_name: userName, filter, page: currentPage, limit: PAGE_SIZE };
            const response = await axios.get<PaginatedImageResponse>(`${API_BASE_URL}/api/images`, { params });
            setImages(response.data.images);
            setRatingChanges({});
        } catch (err: any) {
            setError(err.message || 'An error occurred during submission.');
            console.error(err);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSearch = () => {
        if (!searchInput.trim()) {
            alert("Please enter a filename to search for.");
            return;
        }
        performSearch(searchInput);
    };

    const renderRatingControl = (image: ImageWithRating, ratingName: 'rating1' | 'rating2', label: string) => {
        const currentValue = ratingChanges[image.id]?.[ratingName] ?? image[ratingName];
        return (
            <div className="mb-3">
                <h6>{label}</h6>
                <div>
                    {RATING_OPTIONS.map(value => (
                        <div className="form-check form-check-inline" key={value}>
                            <input className="form-check-input" type="radio" name={`${ratingName}-${image.id}`} id={`${ratingName}-${image.id}-${value}`} value={value} checked={currentValue === value} onChange={() => handleRatingChange(image.id, ratingName, value)} />
                            <label className="form-check-label" htmlFor={`${ratingName}-${image.id}-${value}`}>{value}</label>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const changedCount = Object.keys(ratingChanges).length;

    return (
        <div className="container-fluid mt-4">
            <div className="d-flex justify-content-between align-items-center mb-3 sticky-top bg-light p-3 rounded shadow-sm" style={{ top: '56px' }}>
                <div className="btn-group">
                    <input type="radio" className="btn-check" name="filter" id="filter-all" autoComplete="off" checked={filter === 'all'} onChange={() => setFilter('all')} />
                    <label className="btn btn-outline-secondary" htmlFor="filter-all">All Images</label>
                    <input type="radio" className="btn-check" name="filter" id="filter-unrated" autoComplete="off" checked={filter === 'unrated'} onChange={() => setFilter('unrated')} />
                    <label className="btn btn-outline-secondary" htmlFor="filter-unrated">Unrated</label>
                </div>
                
                <div className="d-flex align-items-center">
                    <div className="input-group me-3">
                        <input 
                            type="text" 
                            className="form-control" 
                            placeholder="Find by filename..." 
                            value={searchInput} 
                            onChange={(e) => setSearchInput(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }}
                        />
                        <button className="btn btn-outline-primary" type="button" onClick={handleSearch}>Find</button>
                    </div>
                    <span className="me-3 text-muted fw-bold">{unratedImages} / {totalImages} images</span>
                    <button className="btn btn-success" onClick={handleSubmitChanges} disabled={isSubmitting || changedCount === 0}>
                        {isSubmitting ? 'Submitting...' : `Submit ${changedCount} Changes`}
                    </button>
                </div>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <div className="d-flex flex-column align-items-center">
                {isLoading ? (
                    <div className="spinner-border" role="status"><span className="visually-hidden">Loading...</span></div>
                ) : images.length > 0 ? (
                    images.map(image => {
                        const isUnrated = image.rating1 === null;
                        const cardClass = filter === 'all' && isUnrated ? "card mb-4 w-100 border-danger border-2" : "card mb-4 w-100";
                        return (
                        <div key={image.id} className={cardClass}>
                            <div className="card-header text-center"><h5 className="mb-0">{image.filename.split('/').pop()}</h5></div>
                            <div className="card-body">
                                <div className="row g-3">
                                    <div className="col-md-9"><img src={`${API_BASE_URL}/${image.path}`} className="img-fluid rounded" alt={image.filename} style={{ maxHeight: '80vh', width: '100%', objectFit: 'contain', backgroundColor: '#f8f9fa' }} /></div>
                                    <div className="col-md-3 d-flex flex-column justify-content-center">
                                        {renderRatingControl(image, 'rating1', 'Rating 1')}
                                        {renderRatingControl(image, 'rating2', 'Rating 2')}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )})
                ) : (
                     <div className="text-center mt-5"><p>No images found for the current filter.</p></div>
                )}
            </div>

            {!isLoading && totalPages > 1 && (
                 <nav className="d-flex justify-content-center align-items-center my-4">
                    <ul className="pagination mb-0">
                        <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}><button className="page-link" onClick={() => setCurrentPage(p => p - 1)}>Previous</button></li>
                        <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}><button className="page-link" onClick={() => setCurrentPage(p => p + 1)}>Next</button></li>
                    </ul>
                    <div className="d-flex align-items-center ms-3">
                        <span className="me-2 text-muted">Page</span>
                        <input type="number" className="form-control" style={{width: "80px"}} value={pageInput} onChange={(e) => setPageInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') handlePageJump(); }} />
                        <span className="mx-2 text-muted">of {totalPages}</span>
                        <button className="btn btn-outline-secondary" onClick={handlePageJump}>Go</button>
                    </div>
                </nav>
            )}
        </div>
    );
};

export default ImageRater;