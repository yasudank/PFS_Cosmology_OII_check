import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';
const PAGE_SIZE = 20;
const RATING_OPTIONS = [0, 1, 2];

interface Image {
    id: number;
    filename: string;
    path: string;
}

interface ImageRaterProps {
    userName: string;
}

interface RatingsState {
    [key: number]: {
        rating1?: number;
        rating2?: number;
    };
}

const ImageRater: React.FC<ImageRaterProps> = ({ userName }) => {
    const [images, setImages] = useState<Image[]>([]);
    const [ratings, setRatings] = useState<RatingsState>({});
    const [remainingCount, setRemainingCount] = useState<number | null>(null);
    const [fetchOffset, setFetchOffset] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [allRated, setAllRated] = useState(false);

    const fetchCount = async () => {
        try {
            const params = { user_name: userName };
            const response = await axios.get<{count: number}>(`${API_BASE_URL}/api/images/count`, { params });
            setRemainingCount(response.data.count);
            if (response.data.count === 0) {
                setImages([]);
                setAllRated(true);
                setError(`All images seem to be rated by you, ${userName}!`);
            }
        } catch (err) {
            console.error("Failed to fetch image count:", err);
        }
    };

    const fetchInitialImages = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const params = {
                user_name: userName,
                skip: 0,
                limit: PAGE_SIZE,
            };
            const response = await axios.get<Image[]>(`${API_BASE_URL}/api/images`, { params });
            
            if (response.data.length > 0) {
                setImages(response.data);
                setFetchOffset(response.data.length);
                const initialRatings: RatingsState = {};
                response.data.forEach(image => {
                    initialRatings[image.id] = {};
                });
                setRatings(initialRatings);
                setAllRated(false);
            } else {
                setImages([]);
                if (remainingCount === 0) {
                     setError(`Welcome, ${userName}! It seems all images have been rated.`);
                }
            }
        } catch (err) {
            setError('Failed to load images. Please make sure the backend server is running.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (userName) {
            fetchCount();
            fetchInitialImages();
        }
    }, [userName]);

    const handleRatingChange = (imageId: number, ratingName: 'rating1' | 'rating2', value: number) => {
        setRatings(prev => ({
            ...prev,
            [imageId]: {
                ...prev[imageId],
                [ratingName]: value,
            },
        }));
    };

    const handleSubmitAllRatings = async () => {
        setIsSubmitting(true);
        setError(null);

        const ratedImagesData = Object.entries(ratings).filter(
            ([_, r]) => r.rating1 !== undefined && r.rating2 !== undefined
        );

        if (ratedImagesData.length === 0) {
            alert("No images have been fully rated on this page.");
            setIsSubmitting(false);
            return;
        }

        const submissionPromises = ratedImagesData.map(([imageId, rating]) => {
            return axios.post(`${API_BASE_URL}/api/images/${Number(imageId)}/rate`, {
                user_name: userName,
                rating1: rating.rating1,
                rating2: rating.rating2,
            });
        });

        try {
            await Promise.all(submissionPromises);
            
            const submittedImageIds = new Set(ratedImagesData.map(([id]) => Number(id)));
            const currentImages = images.filter(image => !submittedImageIds.has(image.id));
            
            setRemainingCount(prev => (prev !== null ? prev - submissionPromises.length : null));

            const newImagesToFetch = submissionPromises.length;
            if (remainingCount !== null && remainingCount > newImagesToFetch) {
                const response = await axios.get<Image[]>(`${API_BASE_URL}/api/images`, {
                    params: {
                        user_name: userName,
                        skip: fetchOffset,
                        limit: newImagesToFetch,
                    },
                });

                if (response.data.length > 0) {
                    setImages([...currentImages, ...response.data]);
                    setFetchOffset(prev => prev + response.data.length);
                    
                    const newRatings: RatingsState = {};
                    response.data.forEach(image => {
                        newRatings[image.id] = {};
                    });
                    setRatings(prev => {
                        const updatedRatings = {...prev};
                        submittedImageIds.forEach(id => delete updatedRatings[id]);
                        return {...updatedRatings, ...newRatings};
                    });
                } else {
                    setImages(currentImages);
                }
            } else {
                 setImages(currentImages);
                 if (currentImages.length === 0) {
                    setAllRated(true);
                    setError(`Congratulations, ${userName}! You have rated all images.`);
                 }
            }

        } catch (err) {
            setError('An error occurred during submission. Some ratings may not have been saved.');
            console.error(err);
        } finally {
            setIsSubmitting(false);
        }
    };

    const renderRatingControl = (imageId: number, ratingName: 'rating1' | 'rating2', label: string) => (
        <div className="mb-3">
            <h6>{label}</h6>
            <div>
                {RATING_OPTIONS.map(value => (
                    <div className="form-check form-check-inline" key={value}>
                        <input
                            className="form-check-input"
                            type="radio"
                            name={`${ratingName}-${imageId}`}
                            id={`${ratingName}-${imageId}-${value}`}
                            value={value}
                            checked={ratings[imageId]?.[ratingName] === value}
                            onChange={() => handleRatingChange(imageId, ratingName, value)}
                        />
                        <label className="form-check-label" htmlFor={`${ratingName}-${imageId}-${value}`}>
                            {value}
                        </label>
                    </div>
                ))}
            </div>
        </div>
    );
    
    const fullyRatedCount = Object.values(ratings).filter(r => r.rating1 !== undefined && r.rating2 !== undefined).length;

    return (
        <div className="container-fluid mt-4">
            <div className="d-flex justify-content-between align-items-center mb-3 sticky-top bg-light p-3 rounded shadow-sm">
                <h2>Rate Images</h2>
                <div className="d-flex align-items-center">
                    {remainingCount !== null && (
                        <span className="badge bg-secondary fs-6 me-3">
                            Remaining: {remainingCount}
                        </span>
                    )}
                    <button 
                        className="btn btn-success"
                        onClick={handleSubmitAllRatings}
                        disabled={isSubmitting || fullyRatedCount === 0}
                    >
                        {isSubmitting ? 'Submitting...' : `Submit ${fullyRatedCount} Rated Images`}
                    </button>
                </div>
            </div>

            {error && <div className={`alert ${allRated ? 'alert-success' : 'alert-info'}`}>{error}</div>}

            <div className="d-flex flex-column align-items-center">
                {isLoading ? (
                    <div className="spinner-border" role="status"><span className="visually-hidden">Loading...</span></div>
                ) : images.length > 0 ? (
                    images.map(image => (
                        <div key={image.id} className="card mb-4 w-100">
                            <div className="card-header text-center">
                                <h5 className="mb-0">{image.filename.split('/').pop()}</h5>
                            </div>
                            <div className="card-body">
                                <div className="row g-3">
                                    <div className="col-md-9">
                                        <img 
                                            src={`${API_BASE_URL}/${image.path}`} 
                                            className="img-fluid rounded" 
                                            alt={image.filename} 
                                            style={{ maxHeight: '80vh', width: '100%', objectFit: 'contain', backgroundColor: '#f8f9fa' }}
                                        />
                                    </div>
                                    <div className="col-md-3 d-flex flex-column justify-content-center">
                                        {renderRatingControl(image.id, 'rating1', 'Rating 1')}
                                        {renderRatingControl(image.id, 'rating2', 'Rating 2')}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                ) : !allRated && !isLoading && (
                     <div className="text-center mt-4">
                        <p>There are no more images to rate.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ImageRater;