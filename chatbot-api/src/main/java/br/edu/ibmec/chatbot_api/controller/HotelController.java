package br.edu.ibmec.chatbot_api.controller;

import java.io.IOException;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import br.edu.ibmec.chatbot_api.integration.AmadeusIntegration;

@RestController
@RequestMapping("/hotels")
public class HotelController {

    private final AmadeusIntegration amadeusIntegration;

    public HotelController(AmadeusIntegration amadeusIntegration) {
        this.amadeusIntegration = amadeusIntegration;
    }

    @GetMapping("searchByCity")
    public ResponseEntity<String> searchHotelsByCity(@RequestParam String destinationCity) throws IOException, InterruptedException {
        return ResponseEntity.ok(amadeusIntegration.searchCityByName(destinationCity, 10));
    }

    @GetMapping("searchHotelsByCityCode")
    public ResponseEntity<String> searchHotelsByCityCode(@RequestParam String cityCode) throws IOException, InterruptedException {
        return ResponseEntity.ok(amadeusIntegration.searchHotelByCity(cityCode));
    }

    @GetMapping("searchByHotelId")
    public ResponseEntity<String> searchOffersByHotelId(@RequestParam String hotelId) throws IOException, InterruptedException {
        return ResponseEntity.ok(amadeusIntegration.searchOffersByHotelId(hotelId));
    }
}
