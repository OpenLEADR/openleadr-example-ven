
const { createApp } = Vue
const RequestApp = {
    data() {
        return {
            request: {
                'title': ''
            },
            requests: []
        }
    },
    async created() {
        await this.getRequests()
    },
    methods: {
        async sendRequest(url, method, data) {
            const myHeaders = new Headers({
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            })

            const response = await fetch(url, {
                method: method,
                headers: myHeaders,
                body: data
            })
            return response
        },
        async getRequests() {
            const response = await this.sendRequest(window.location, 'get')
            this.requests = await response.json()
        },

        // X buttons on dashboar hit the Flask
        // endpoint for release individual overrides
         parseMe(requestStr) {
            const myArray = requestStr.title.split(' ');
            console.log('requestStr: ' + requestStr)

            var release_dict = {
                address: null,
                object_type: null,
                object_instance: null,
                priority: null,
                id: null
            };

            for (var i = 0; i < myArray.length; i++) {
                console.log(myArray[i], i)
                if (i == 0) {
                    release_dict.address = myArray[i];
                } else if (i == 1) {
                    release_dict.object_type = myArray[i];
                } else if (i == 2) {
                    release_dict.object_instance = myArray[i];
                } else if (i == 6) {
                    release_dict.priority = myArray[i];
                } else {}
            }
            release_dict.id = requestStr.id
            return release_dict

        },
        async deleteRequest(request) {
            await this.sendRequest(window.location + 'bacnet/release/','post',JSON.stringify(this.parseMe(request)))
            await this.getRequests()
        },
    },
    delimiters: ['{', '}']
}

createApp(RequestApp).mount('#app')