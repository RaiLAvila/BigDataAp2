package br.edu.ibmec.chatbot_api.repository;

import java.util.List;

import org.springframework.stereotype.Repository;

import com.azure.spring.data.cosmos.repository.CosmosRepository;

import br.edu.ibmec.chatbot_api.models.ReservaHotel;

@Repository
public interface ReservaHotelRepository extends CosmosRepository<ReservaHotel, String> {
    List<ReservaHotel> findByClienteCpf(String cpf);
}
