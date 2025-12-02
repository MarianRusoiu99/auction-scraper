function listingsApp() {
    return {
        listings: [],
        subscriptions: [],
        loading: false,
        view: 'grid', // 'grid', 'list', or 'detail'
        selectedListing: null,
        subscriptionEmail: '',

        filters: {
            search: '',
            category: '',
            min_price: '',
            max_price: '',
            county: '',
            city: '',
            status_unsold: false,
            status_active: false,
            page: 1,
            page_size: 12
        },

        init() {
            this.fetchListings();
            this.fetchSubscriptions();

            // Handle browser back button for detail view
            window.addEventListener('popstate', (event) => {
                if (this.view === 'detail') {
                    this.closeDetail();
                }
            });
        },

        async fetchListings() {
            this.loading = true;
            try {
                // Build query string
                const params = new URLSearchParams();

                // Handle standard filters
                if (this.filters.search) params.append('search', this.filters.search);
                if (this.filters.category) params.append('category', this.filters.category);
                if (this.filters.min_price) params.append('min_price', this.filters.min_price);
                if (this.filters.max_price) params.append('max_price', this.filters.max_price);
                if (this.filters.county) params.append('county', this.filters.county);
                if (this.filters.city) params.append('city', this.filters.city);

                // Handle checkbox filters
                if (this.filters.status_unsold) {
                    params.append('status', 'NEADJUDECAT');
                }
                if (this.filters.status_active) {
                    params.append('auction_status', 'Licitatie in desfasurare');
                }

                params.append('page', this.filters.page);
                params.append('page_size', this.filters.page_size);

                const response = await fetch(`/listings/?${params.toString()}`);
                if (!response.ok) throw new Error('Failed to fetch listings');

                this.listings = await response.json();

                // Scroll to top
                document.querySelector('.main-content').scrollTop = 0;
            } catch (error) {
                console.error('Error fetching listings:', error);
                alert('Error loading listings. Please try again.');
            } finally {
                this.loading = false;
            }
        },

        async fetchSubscriptions() {
            try {
                const response = await fetch('/subscriptions/');
                if (!response.ok) throw new Error('Failed to fetch subscriptions');
                this.subscriptions = await response.json();
            } catch (error) {
                console.error('Error fetching subscriptions:', error);
            }
        },

        async subscribe() {
            if (!this.subscriptionEmail) return;

            try {
                const payload = {
                    email: this.subscriptionEmail,
                    filters: { ...this.filters } // Copy current filters
                };

                // Remove pagination and internal flags
                delete payload.filters.page;
                delete payload.filters.page_size;
                delete payload.filters.status_unsold;
                delete payload.filters.status_active;

                // Map checkboxes to backend fields for subscription
                if (this.filters.status_unsold) payload.filters.status = 'NEADJUDECAT';
                if (this.filters.status_active) payload.filters.auction_status = 'Licitatie in desfasurare';

                const response = await fetch('/subscriptions/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) throw new Error('Failed to subscribe');

                const newSub = await response.json();
                this.subscriptions.push(newSub);
                this.subscriptionEmail = ''; // Clear input
                alert('Successfully subscribed to notifications!');
            } catch (error) {
                console.error('Error subscribing:', error);
                alert('Failed to subscribe. Please try again.');
            }
        },

        async deleteSubscription(id) {
            if (!confirm('Are you sure you want to unsubscribe?')) return;

            try {
                const response = await fetch(`/subscriptions/${id}`, {
                    method: 'DELETE',
                });

                if (!response.ok) throw new Error('Failed to delete subscription');

                this.subscriptions = this.subscriptions.filter(sub => sub.id !== id);
            } catch (error) {
                console.error('Error deleting subscription:', error);
                alert('Failed to unsubscribe.');
            }
        },

        resetFilters() {
            this.filters = {
                search: '',
                category: '',
                min_price: '',
                max_price: '',
                county: '',
                city: '',
                status_unsold: false,
                status_active: false,
                page: 1,
                page_size: 12
            };
            this.fetchListings();
        },

        nextPage() {
            this.filters.page++;
            this.fetchListings();
        },

        prevPage() {
            if (this.filters.page > 1) {
                this.filters.page--;
                this.fetchListings();
            }
        },

        openDetail(listing) {
            this.selectedListing = listing;
            this.view = 'detail';
            window.history.pushState({ view: 'detail', id: listing.id }, '', `#listing-${listing.id}`);
            document.querySelector('.main-content').scrollTop = 0;
        },

        closeDetail() {
            this.selectedListing = null;
            this.view = 'grid'; // Default back to grid, or remember previous view
            window.history.pushState({}, '', '/');
        },

        formatCurrency(value) {
            if (value === null || value === undefined || value === '') return 'N/A';
            // If value is already a string, return it as-is
            if (typeof value === 'string') {
                return value;
            }
            return new Intl.NumberFormat('ro-RO', {
                style: 'currency',
                currency: 'RON'
            }).format(value);
        },

        formatDate(dateString) {
            if (!dateString) return 'N/A';
            return new Date(dateString).toLocaleDateString('ro-RO');
        },

        formatDateTime(dateString) {
            if (!dateString) return 'N/A';
            return new Date(dateString).toLocaleString('ro-RO');
        },

        truncate(text, length) {
            if (!text) return '';
            if (text.length <= length) return text;
            return text.substring(0, length) + '...';
        }
    }
}
