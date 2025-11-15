package br.edu.ibmec.chatbot_api.controller;

import java.io.IOException;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import br.edu.ibmec.chatbot_api.integration.AmadeusIntegration;

@RestController
@RequestMapping("/flights")
public class FlightController {

    private final AmadeusIntegration amadeusIntegration;

    public FlightController(AmadeusIntegration amadeusIntegration) {
        this.amadeusIntegration = amadeusIntegration;
    }

    @GetMapping("search")
    public ResponseEntity<String> searchFlights(@RequestParam String origin, @RequestParam String destination, @RequestParam String departureDate, @RequestParam String adults) throws IOException, InterruptedException {
        return ResponseEntity.ok(amadeusIntegration.searchFlightOffers(origin, destination, departureDate, adults));
    }
}
