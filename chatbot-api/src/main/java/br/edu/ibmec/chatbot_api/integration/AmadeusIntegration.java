package br.edu.ibmec.chatbot_api.integration;

import java.io.IOException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class AmadeusIntegration {
    private static final String BASE_URL = "https://test.api.amadeus.com/";
    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    @Value("${amadeus.client.id}")
    private String clientId;

    @Value("${amadeus.client.secret}")
    private String clientSecret;
    
    private String accessToken;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    private static final Logger logger = LoggerFactory.getLogger(AmadeusIntegration.class);

    public AmadeusIntegration() {
        this.httpClient = HttpClient.newHttpClient();
        this.objectMapper = new ObjectMapper();
    }

    public void authenticate() throws IOException, InterruptedException {
        String body = "grant_type=client_credentials&client_id=" + clientId 
                      + "&client_secret=" + clientSecret;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(java.net.URI.create(BASE_URL + "v1/security/oauth2/token"))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        var response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        JsonNode jsonResponse = objectMapper.readTree(response.body());

        if (response.statusCode() != 200) {
            throw new IOException("Failed to authenticate with Amadeus API: " + jsonResponse.toString());
        }

        this.accessToken = jsonResponse.get("access_token").asText();
        logger.info("Access Token: {}", this.accessToken);
    }

    public String searchHotelByCity(String cityCode) throws IOException, InterruptedException {
        if (accessToken == null) 
            this.authenticate();
        
        String url = BASE_URL + "v3/shopping/hotel-offers?cityCode=" + cityCode;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(java.net.URI.create(url))
                .header(AUTHORIZATION_HEADER, BEARER_PREFIX + accessToken)
                .GET()
                .build();
        var response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        return response.body();
    }

    public String searchCityByName(String cityName, int limit) throws IOException, InterruptedException {
        if (accessToken == null) 
            this.authenticate();
        
        String url = BASE_URL + "v1/reference-data/locations?subType=CITY&keyword=" + cityName
                              + "&view=LIGHT"
                              + "&page[limit]=" + limit;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(java.net.URI.create(url))
                .header(AUTHORIZATION_HEADER, BEARER_PREFIX + accessToken)
                .GET()
                .build();
        var response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        return response.body();
    }

    public String getOfferPricing(String offerId) throws IOException, InterruptedException {
        if (accessToken == null) 
            this.authenticate();
        
        String url = BASE_URL + "v3/shopping/hotel-offers/" + offerId;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(java.net.URI.create(url))
                .header(AUTHORIZATION_HEADER, BEARER_PREFIX + accessToken)
                .GET()
                .build();
                
        var response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        return response.body();
    }

    public String searchFlightOffers(String origin, String destination, String departureDate, String adults) throws IOException, InterruptedException {
        if (accessToken == null) 
            this.authenticate();
        
        String url = BASE_URL + "v2/shopping/flight-offers?originLocationCode=" + origin 
                      + "&destinationLocationCode=" + destination
                      + "&departureDate=" + departureDate
                      + "&adults=" + adults;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(java.net.URI.create(url))
                .header(AUTHORIZATION_HEADER, BEARER_PREFIX + accessToken)
                .GET()
                .build();
                
        var response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        return response.body();
    }
}
