package br.edu.ibmec.chatbot_api.repository;

import java.util.List;

import org.springframework.stereotype.Repository;

import com.azure.spring.data.cosmos.repository.CosmosRepository;

import br.edu.ibmec.chatbot_api.models.ReservaVoo;

@Repository
public interface ReservaVooRepository extends CosmosRepository<ReservaVoo, String> {
    List<ReservaVoo> findByClienteCpf(String cpf);
}
